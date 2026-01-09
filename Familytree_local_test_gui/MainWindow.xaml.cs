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
            // 防止重复点击，UI 上临时禁用开始按钮，最终由 UpdateButtons 决定最终状态
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
            finally { UpdateButtons(); }
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
            UpdateButtons();
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
            // 当进程退出时，从字典中移除并更新按钮状态（在 UI 线程执行）
            proc.Exited += (_, _) =>
            {
                Dispatcher.Invoke(() =>
                {
                    Log(role, "进程已退出");
                    try { _running.Remove(scriptPath); } catch { /* ignore */ }
                    UpdateButtons();
                });
            };

            proc.Start();
            // 异步处理标准输出和错误流，解决中文乱码
            _ = ReadStreamWithEncodingDetectionAsync(proc.StandardOutput.BaseStream, role, isError: false);
            _ = ReadStreamWithEncodingDetectionAsync(proc.StandardError.BaseStream, role, isError: true);

            _running[scriptPath] = proc;
            Log(role, "✅ 已启动");
            UpdateButtons();
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
        /// 修复点：当输出很短（&lt; 检测阈值）且进程结束时会丢失剩余字节，导致未能匹配 "Running on ..." 并打开浏览器。
        /// 这里在流结束时即使未检测到编码也会尝试使用检测/回退 UTF8 来冲刷剩余字节并查找 URL。
        /// 同时改进 URL 提取、增加日志，以及统一通过 OpenUrlSafely 打开浏览器（含备用方案）。
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
                            // 优先用 "Running on ..." 查找 URL
                            var match = System.Text.RegularExpressions.Regex.Match(
                                logText,
                                @"Running on\s+(https?://[^\s\)\]\\""]+)",
                                System.Text.RegularExpressions.RegexOptions.IgnoreCase);
                            if (match.Success)
                            {
                                string url = TrimUrl(match.Groups[1].Value);
                                Log("client", $"检测到 URL：{url}");
                                OpenUrlSafely(url);
                            }
                            else
                            {
                                // 作为补充：尝试直接查找任意 http(s) URL（并排除尾随符号）
                                var urlMatch = System.Text.RegularExpressions.Regex.Match(
                                    logText,
                                    @"https?://[^\s\)\]\\""]+",
                                    System.Text.RegularExpressions.RegexOptions.IgnoreCase);
                                if (urlMatch.Success)
                                {
                                    string url = TrimUrl(urlMatch.Value);
                                    Log("client", $"检测到 URL（备用规则）：{url}");
                                    OpenUrlSafely(url);
                                }
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

                // 流读取完毕：无论是否已检测出编码，都尝试冲刷剩余字节并处理文本（修复短输出被丢弃的问题）
                if (leftoverBuffer.Length > 0)
                {
                    var remainingBytes = leftoverBuffer.ToArray();

                    if (!encodingDetected)
                    {
                        // 即使不到阈值，也根据现有字节尝试检测编码（若检测失败，DetectStreamEncoding 会回退到 UTF8）
                        detectedEncoding = DetectStreamEncoding(remainingBytes);
                    }

                    string finalText;
                    try
                    {
                        finalText = detectedEncoding.GetString(remainingBytes);
                    }
                    catch
                    {
                        finalText = Encoding.UTF8.GetString(remainingBytes);
                    }

                    if (!string.IsNullOrEmpty(finalText))
                    {
                        Log(role, isError ? $"ERR: {finalText}" : finalText);
                        if (role == "client" && !isError)
                        {
                            var match = System.Text.RegularExpressions.Regex.Match(
                                finalText,
                                @"Running on\s+(https?://[^\s\)\]\\""]+)",
                                System.Text.RegularExpressions.RegexOptions.IgnoreCase);
                            if (match.Success)
                            {
                                string url = TrimUrl(match.Groups[1].Value);
                                Log("client", $"检测到 URL（流结束）：{url}");
                                OpenUrlSafely(url);
                            }
                            else
                            {
                                var urlMatch = System.Text.RegularExpressions.Regex.Match(
                                    finalText,
                                    @"https?://[^\s\)\]\\""]+",
                                    System.Text.RegularExpressions.RegexOptions.IgnoreCase);
                                if (urlMatch.Success)
                                {
                                    string url = TrimUrl(urlMatch.Value);
                                    Log("client", $"检测到 URL（流结束-备用）：{url}");
                                    OpenUrlSafely(url);
                                }
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
        /// 统一安全打开 URL：先尝试 UseShellExecute = true，失败后尝试通过 cmd start 作为回退。
        /// 并记录完整异常信息到日志，便于排查。
        /// </summary>
        private void OpenUrlSafely(string url)
        {
            if (string.IsNullOrWhiteSpace(url)) return;

            Dispatcher.Invoke(() =>
            {
                string cleaned = TrimUrl(url);
                Log("client", $"尝试打开浏览器：{cleaned}");
                try
                {
                    Process.Start(new ProcessStartInfo(cleaned) { UseShellExecute = true });
                    Log("client", "✅ 已调用系统打开浏览器");
                }
                catch (Exception ex)
                {
                    Log("client", $"❌ 使用 Shell 打开失败：{ex.Message}。尝试备用方式...");
                    try
                    {
                        // 备用方式：cmd /c start "" "url"
                        string escaped = cleaned.Replace("\"", "\\\"");
                        // 使用 CreateNoWindow 并让 cmd 去启动默认浏览器
                        Process.Start(new ProcessStartInfo("cmd", $"/c start \"\" \"{escaped}\"")
                        {
                            CreateNoWindow = true,
                            UseShellExecute = false
                        });
                        Log("client", "✅ 备用方式已调用 cmd start 打开浏览器");
                    }
                    catch (Exception ex2)
                    {
                        Log("client", $"❌ 备用打开失败：{ex2.Message}");
                        Log("client", ex2.ToString());
                    }
                }
            });
        }

        private static string TrimUrl(string url)
        {
            if (string.IsNullOrWhiteSpace(url)) return url;
            return url.Trim().TrimEnd('.', ',', ';', ')', ']', '"', '\'');
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

        /* ===================== 按钮状态管理 ===================== */

        /// <summary>
        /// 根据当前是否有运行中的进程，切换 Start / Stop 按钮启用状态。
        /// 未运行时禁用 Stop，运行时禁用 Start。
        /// </summary>
        private void UpdateButtons()
        {
            Dispatcher.Invoke(() =>
            {
                bool running = _running.Values.Any(p => !p.HasExited);
                StartButton.IsEnabled = !running;
                StopButton.IsEnabled = running;
            });
        }

        protected override void OnInitialized(EventArgs e)
        {
            base.OnInitialized(e);
            UpdateButtons();
        }
    }
}