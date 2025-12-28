using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;


namespace WpfFadeInDemo
{
    public partial class MainWindow : Window
    {
        private readonly Dictionary<string, Process> _running = new();
        private DateTime _lastIpChangeTime;
        private const int AutoSaveDelayMs = 1000; // 1秒自动保存延迟


        /* ===================== 启动 / 停止 ===================== */

        private async void StartButton_Click(object sender, RoutedEventArgs e)
        {
            StartButton.IsEnabled = false;
            try
            {
                string? root = FindProjectRoot(AppDomain.CurrentDomain.BaseDirectory);
                if (root == null) { Log("server", "❌ 未找到项目根目录"); return; }

                // 确保路径始终包含../
                string serverPy = Path.GetFullPath(Path.Combine(root, "..", "server", "app.py"));
                string clientPy = Path.GetFullPath(Path.Combine(root, "..", "client", "app.py"));

                if (!File.Exists(serverPy)) { Log("server", "❌ 服务端脚本不存在"); return; }
                if (!File.Exists(clientPy)) { Log("client", "❌ 客户端脚本不存在"); return; }

                StartScript(serverPy, "server");
                await Task.Delay(3000);
                StartScript(clientPy, "client");
            }
            catch (Exception ex) { Log("server", $"❌ {ex.Message}"); }
            finally { StartButton.IsEnabled = true; }
        }

        private void StopButton_Click(object sender, RoutedEventArgs e)
        {
            foreach (var kv in _running.ToList())
            {
                try
                {
                    if (!kv.Value.HasExited)
                    {
                        kv.Value.Kill(entireProcessTree: true);
                        Log(kv.Key.Contains("server") ? "server" : "client", "已停止");
                    }
                }
                catch { /* ignore */ }
            }
            _running.Clear();
        }

        private void Window_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            StopButton_Click(null, null);
        }

        /* ===================== 进程启动（修复中文乱码） ===================== */

        private void StartScript(string scriptPath, string role)
        {
            if (_running.TryGetValue(scriptPath, out var old) && !old.HasExited)
            {
                Log(role, "⚠️ 已在运行");
                return;
            }

            string? venv = FindVenvPython(Path.GetDirectoryName(scriptPath));
            if (venv == null) { Log(role, "❌ 未找到 venv"); return; }

            var psi = new ProcessStartInfo
            {
                FileName = venv,
                Arguments = $"\"{scriptPath}\"",
                WorkingDirectory = Path.GetDirectoryName(scriptPath)!,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                // 移除硬编码UTF8，改为通过字节流检测编码
            };

            var proc = new Process { StartInfo = psi, EnableRaisingEvents = true };
            // 移除原有同步日志绑定，改为异步编码检测读取
            proc.Exited += (_, _) => Log(role, "进程已退出");

            proc.Start();
            // 异步处理标准输出和错误流，解决中文乱码
            _ = ReadStreamWithEncodingDetectionAsync(proc.StandardOutput.BaseStream, role, isError: false);
            _ = ReadStreamWithEncodingDetectionAsync(proc.StandardError.BaseStream, role, isError: true);

            _running[scriptPath] = proc;
            Log(role, "✅ 已启动");
        }

        private static string? FindVenvPython(string? dir) =>
            dir == null ? null :
            File.Exists(Path.Combine(dir, "venv", "Scripts", "python.exe"))
                ? Path.Combine(dir, "venv", "Scripts", "python.exe")
                : null;

        private static string? FindProjectRoot(string start)
        {
            var d = new DirectoryInfo(start);
            while (d != null)
            {
                if (d.EnumerateFiles("*.csproj").Any()) return d.FullName;
                d = d.Parent;
            }
            return null;
        }

        /* ===================== 编码检测与日志读取（核心修复） ===================== */

        /// <summary>
        /// 异步读取流并自动检测编码，解决中文乱码
        /// </summary>
        private async Task ReadStreamWithEncodingDetectionAsync(Stream stream, string role, bool isError)
        {
            const int bufferSize = 4096;
            var buffer = new byte[bufferSize];
            int bytesRead;
            bool encodingDetected = false;
            Encoding detectedEncoding = Encoding.UTF8;
            Decoder decoder = null;
            var leftoverBuffer = new MemoryStream(); // 保存未完整解码的字节

            try
            {
                while ((bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length)) > 0)
                {
                    // 将本次读取的字节存入缓冲，处理跨块的多字节字符
                    leftoverBuffer.Write(buffer, 0, bytesRead);
                    var totalBytes = leftoverBuffer.ToArray();

                    // 未检测编码时，累积足够字节再检测（至少64字节，避免误判）
                    if (!encodingDetected)
                    {
                        if (totalBytes.Length < 64 && stream.CanRead)
                        {
                            continue;
                        }
                        detectedEncoding = DetectStreamEncoding(totalBytes);
                        decoder = detectedEncoding.GetDecoder();
                        encodingDetected = true;
                    }

                    // 使用检测到的编码解码，处理不完整字符
                    int charCount = decoder.GetCharCount(totalBytes, 0, totalBytes.Length, flush: false);
                    var chars = new char[charCount];
                    decoder.Convert(totalBytes, 0, totalBytes.Length, chars, 0, chars.Length, false, out int bytesUsed, out int charsUsed, out _);

                    // 输出解码后的文本
                    if (charsUsed > 0)
                    {
                        string logText = new string(chars, 0, charsUsed);
                        Log(role, isError ? $"ERR: {logText}" : logText);
                        if (role == "client" && !isError)
                        {
                            var match = System.Text.RegularExpressions.Regex.Match(
                                logText,
                                @"Running on\s+(https?://[^\s]+)",
                                System.Text.RegularExpressions.RegexOptions.IgnoreCase);
                            if (match.Success)
                            {
                                string url = match.Groups[1].Value;
                                // 必须在 UI 线程打开浏览器
                                Dispatcher.Invoke(() =>
                                {
                                    try { Process.Start(new ProcessStartInfo(url) { UseShellExecute = true }); }
                                    catch (Exception ex) { Log("client", $"❌ 自动打开浏览器失败：{ex.Message}"); }
                                });
                            }
                        }
                    }

                    

                    // 保留未使用的字节（不完整字符），用于下次解码
                    leftoverBuffer.SetLength(0);
                    if (bytesUsed < totalBytes.Length)
                    {
                        leftoverBuffer.Write(totalBytes, bytesUsed, totalBytes.Length - bytesUsed);
                    }
                }

                // 流读取完毕，冲刷剩余字节
                if (leftoverBuffer.Length > 0 && encodingDetected)
                {
                    var remainingBytes = leftoverBuffer.ToArray();
                    string finalText = detectedEncoding.GetString(remainingBytes);
                    if (!string.IsNullOrEmpty(finalText))
                    {
                        Log(role, isError ? $"ERR: {finalText}" : finalText);
                        if (role == "client" && !isError)
                        {
                            var match = System.Text.RegularExpressions.Regex.Match(
                                finalText,
                                @"Running on\s+(https?://[^\s]+)",
                                System.Text.RegularExpressions.RegexOptions.IgnoreCase);
                            if (match.Success)
                            {
                                string url = match.Groups[1].Value;
                                Dispatcher.Invoke(() =>
                                {
                                    try { Process.Start(new ProcessStartInfo(url) { UseShellExecute = true }); }
                                    catch (Exception ex) { Log("client", $"❌ 自动打开浏览器失败：{ex.Message}"); }
                                });
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                if (!ex.Message.Contains("closed", StringComparison.OrdinalIgnoreCase))
                {
                    Log(role, $"❌ 日志读取失败：{ex.Message}");
                }
            }
        }

        /// <summary>
        /// 检测字节流的编码（优先UTF8，再GBK，最后默认UTF8）
        /// </summary>
        private static Encoding DetectStreamEncoding(byte[] data)
        {
            if (data == null || data.Length == 0)
            {
                return Encoding.UTF8;
            }

            // 检测UTF8（无替换字符则为UTF8）
            try
            {
                string utf8Text = Encoding.UTF8.GetString(data);
                if (!ContainsUnicodeReplacementChar(utf8Text))
                {
                    return Encoding.UTF8;
                }
            }
            catch
            {
                // UTF8解码失败，尝试GBK
            }

            // 检测GBK（Windows中文环境默认编码）
            try
            {
                var gbkEncoding = Encoding.GetEncoding("GBK");
                string gbkText = gbkEncoding.GetString(data);
                if (!string.IsNullOrEmpty(gbkText))
                {
                    return gbkEncoding;
                }
            }
            catch
            {
                // GBK解码失败，退回UTF8
            }

            return Encoding.UTF8;
        }

        /// <summary>
        /// 检查字符串是否包含Unicode替换字符（�），用于判断编码是否正确
        /// </summary>
        private static bool ContainsUnicodeReplacementChar(string text)
        {
            return string.IsNullOrEmpty(text) ? false : text.IndexOf('\uFFFD') != -1;
        }

        /* ===================== 日志输出 ===================== */

        private void Log(string role, string msg)
        {
            Dispatcher.Invoke(() =>
            {
                // 补充换行符，确保日志分行显示
                string line = $"[{DateTime.Now:HH:mm:ss}] {msg}{Environment.NewLine}";
                if (role == "server")
                {
                    ServerLogBox.AppendText(line);
                    ServerLogBox.ScrollToEnd();
                }
                else
                {
                    ClientLogBox.AppendText(line);
                    ClientLogBox.ScrollToEnd();
                }
            });
        }
    }
}