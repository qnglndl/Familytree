using System;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Threading.Tasks;
using Microsoft.Win32;

// SSH.NET 引用
using Renci.SshNet;
using Renci.SshNet.Common;

namespace Connect_to_server_gui
{
    public partial class MainWindow : Window
    {
        private bool isConnecting = false;
        private string selectedKeyFilePath = "";

        public MainWindow()
        {
            InitializeComponent();

            // 设置初始状态
            NoAuthRadio.IsChecked = true;
            PasswordInput.IsEnabled = false;
            KeySelectButton.IsEnabled = false;
            ServerIpInput.Foreground = Brushes.Gray;

            // 绑定事件
            AttachEvents();

            // 立即开始启动动画
            StartWelcomeAnimation();
        }

        private void AttachEvents()
        {
            ServerIpInput.GotFocus += ServerIpInput_GotFocus;
            ServerIpInput.LostFocus += ServerIpInput_LostFocus;
            NoAuthRadio.Checked += AuthenticationMethod_Changed;
            PasswordRadio.Checked += AuthenticationMethod_Changed;
            KeyRadio.Checked += AuthenticationMethod_Changed;
            KeySelectButton.Click += KeySelectButton_Click;
            ConnectButton.Click += ConnectButton_Click;
            CloseResultButton.Click += CloseResultButton_Click;
        }

        private async void StartWelcomeAnimation()
        {
            // 欢迎文字淡入
            var welcomeFadeIn = new DoubleAnimation
            {
                From = 0,
                To = 1,
                Duration = TimeSpan.FromSeconds(1)
            };
            WelcomeText.BeginAnimation(UIElement.OpacityProperty, welcomeFadeIn);

            await Task.Delay(2000);

            // 欢迎文字淡出
            var welcomeFadeOut = new DoubleAnimation
            {
                From = 1,
                To = 0,
                Duration = TimeSpan.FromSeconds(0.5)
            };
            WelcomeText.BeginAnimation(UIElement.OpacityProperty, welcomeFadeOut);

            await Task.Delay(500);

            // 显示连接面板
            var panelFadeIn = new DoubleAnimation
            {
                From = 0,
                To = 1,
                Duration = TimeSpan.FromSeconds(0.5)
            };
            ConnectionPanel.BeginAnimation(UIElement.OpacityProperty, panelFadeIn);
        }

        private void ServerIpInput_GotFocus(object sender, RoutedEventArgs e)
        {
            if (ServerIpInput.Text == "用户名@服务器IP")
            {
                ServerIpInput.Text = "";
                ServerIpInput.Foreground = Brushes.Black;
            }
        }

        private void ServerIpInput_LostFocus(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(ServerIpInput.Text))
            {
                ServerIpInput.Text = "用户名@服务器IP";
                ServerIpInput.Foreground = Brushes.Gray;
            }
        }

        private void AuthenticationMethod_Changed(object sender, RoutedEventArgs e)
        {
            PasswordInput.IsEnabled = PasswordRadio.IsChecked == true;
            KeySelectButton.IsEnabled = KeyRadio.IsChecked == true;
        }

        private void KeySelectButton_Click(object sender, RoutedEventArgs e)
        {
            var openFileDialog = new OpenFileDialog
            {
                Filter = "密钥文件 (*.pem;*.ppk)|*.pem;*.ppk|所有文件 (*.*)|*.*",
                Title = "选择SSH密钥文件",
                Multiselect = false
            };

            if (openFileDialog.ShowDialog() == true)
            {
                selectedKeyFilePath = openFileDialog.FileName;
                KeyFilePathText.Text = Path.GetFileName(selectedKeyFilePath);
                KeyFilePathText.ToolTip = selectedKeyFilePath;
            }
        }

        private async void ConnectButton_Click(object sender, RoutedEventArgs e)
        {
            if (isConnecting) return;

            // 验证输入
            var serverInput = ServerIpInput.Text.Trim();
            if (serverInput == "用户名@服务器IP" || string.IsNullOrWhiteSpace(serverInput))
            {
                ShowMessage("错误", "请输入服务器地址！", false);
                ServerIpInput.Focus();
                return;
            }

            if (!serverInput.Contains('@'))
            {
                ShowMessage("错误", "请输入正确的格式：用户名@服务器IP", false);
                ServerIpInput.Focus();
                return;
            }

            // 解析用户名和主机名
            var parts = serverInput.Split('@');
            var username = parts[0];
            var hostname = parts[1];

            // 解析端口
            if (!int.TryParse(PortInput.Text.Trim(), out int port))
            {
                port = 22;
            }

            if (port <= 0 || port > 65535)
            {
                ShowMessage("错误", "请输入有效的端口号（1-65535）！", false);
                PortInput.Focus();
                return;
            }

            // 验证认证方式
            if (PasswordRadio.IsChecked == true && string.IsNullOrEmpty(PasswordInput.Password))
            {
                ShowMessage("错误", "请输入密码！", false);
                PasswordInput.Focus();
                return;
            }

            if (KeyRadio.IsChecked == true && (string.IsNullOrEmpty(selectedKeyFilePath) || !File.Exists(selectedKeyFilePath)))
            {
                ShowMessage("错误", "请选择有效的密钥文件！", false);
                return;
            }

            // 开始连接
            isConnecting = true;
            await ShowLoading(true);

            try
            {
                bool success = false;
                string message = "";

                if (NoAuthRadio.IsChecked == true)
                {
                    (success, message) = await ConnectWithNoAuth(hostname, port, username);
                }
                else if (PasswordRadio.IsChecked == true)
                {
                    (success, message) = await ConnectWithPassword(hostname, port, username, PasswordInput.Password);
                }
                else if (KeyRadio.IsChecked == true)
                {
                    (success, message) = await ConnectWithKey(hostname, port, username, selectedKeyFilePath);
                }

                await ShowLoading(false);

                ShowMessage(success ? "成功" : "失败", message, success);
            }
            catch (Exception ex)
            {
                await ShowLoading(false);
                ShowMessage("异常", $"连接异常：{ex.Message}", false);
            }
            finally
            {
                isConnecting = false;
            }
        }

        private async Task<(bool success, string message)> ConnectWithNoAuth(string hostname, int port, string username)
        {
            return await Task.Run(() =>
            {
                try
                {
                    // 测试端口连接性
                    using (var client = new System.Net.Sockets.TcpClient())
                    {
                        var result = client.BeginConnect(hostname, port, null, null);
                        var success = result.AsyncWaitHandle.WaitOne(TimeSpan.FromSeconds(5));

                        if (success)
                        {
                            client.EndConnect(result);
                            client.Close();
                            return (true,
                                $"✅ 端口连接成功\n\n" +
                                $"🔗 服务器: {hostname}:{port}\n" +
                                $"👤 用户: {username}\n" +
                                $"🔐 认证方式: 无密码\n" +
                                $"📊 状态: SSH端口可访问\n\n" +
                                $"💡 提示: 服务器需要配置免密码SSH登录");
                        }
                        else
                        {
                            return (false, "❌ 连接超时：5秒内无响应");
                        }
                    }
                }
                catch (Exception ex)
                {
                    return (false, $"❌ 连接失败：{ex.Message}");
                }
            });
        }

        private async Task<(bool success, string message)> ConnectWithPassword(string hostname, int port, string username, string password)
        {
            return await Task.Run(() =>
            {
                try
                {
                    using (var client = new SshClient(hostname, port, username, password))
                    {
                        client.Connect();

                        if (client.IsConnected)
                        {
                            // 获取服务器信息
                            var hostnameCmd = client.RunCommand("hostname");
                            var whoamiCmd = client.RunCommand("whoami");
                            var osCmd = client.RunCommand("uname -a");
                            var diskCmd = client.RunCommand("df -h / | tail -1");

                            client.Disconnect();

                            return (true,
                                $"✅ SSH连接成功\n\n" +
                                $"🔗 服务器: {hostname}:{port}\n" +
                                $"👤 用户: {username}\n" +
                                $"🔐 认证方式: 密码\n" +
                                $"📊 状态: 已连接\n\n" +
                                $"📋 服务器信息:\n" +
                                $"   主机名: {hostnameCmd.Result.Trim()}\n" +
                                $"   当前用户: {whoamiCmd.Result.Trim()}\n" +
                                $"   系统信息: {osCmd.Result.Trim()}\n" +
                                $"   磁盘使用: {diskCmd.Result.Trim()}");
                        }
                        else
                        {
                            return (false, "❌ 连接失败：无法建立SSH连接");
                        }
                    }
                }
                // 修复这里：使用 SshAuthenticationException 而不是 AuthenticationException
                catch (SshAuthenticationException ex)
                {
                    return (false, $"❌ 认证失败：用户名或密码错误\n\n{ex.Message}");
                }
                catch (SshConnectionException ex)
                {
                    return (false, $"❌ 连接异常：{ex.Message}");
                }
                catch (Exception ex)
                {
                    return (false, $"❌ 连接失败：{ex.Message}");
                }
            });
        }

        private async Task<(bool success, string message)> ConnectWithKey(string hostname, int port, string username, string keyFilePath)
        {
            return await Task.Run(() =>
            {
                try
                {
                    // 读取密钥文件
                    var keyFile = new PrivateKeyFile(keyFilePath);
                    var keyFiles = new[] { keyFile };

                    var connectionInfo = new ConnectionInfo(
                        hostname,
                        port,
                        username,
                        new PrivateKeyAuthenticationMethod(username, keyFiles)
                    );

                    using (var client = new SshClient(connectionInfo))
                    {
                        client.Connect();

                        if (client.IsConnected)
                        {
                            // 获取服务器信息
                            var hostnameCmd = client.RunCommand("hostname");
                            var whoamiCmd = client.RunCommand("whoami");
                            var uptimeCmd = client.RunCommand("uptime -p");
                            var memoryCmd = client.RunCommand("free -h | grep Mem");

                            client.Disconnect();

                            return (true,
                                $"✅ SSH连接成功\n\n" +
                                $"🔗 服务器: {hostname}:{port}\n" +
                                $"👤 用户: {username}\n" +
                                $"🔐 认证方式: 密钥文件\n" +
                                $"🗝️ 密钥文件: {Path.GetFileName(keyFilePath)}\n" +
                                $"📊 状态: 已连接\n\n" +
                                $"📋 服务器信息:\n" +
                                $"   主机名: {hostnameCmd.Result.Trim()}\n" +
                                $"   当前用户: {whoamiCmd.Result.Trim()}\n" +
                                $"   运行时间: {uptimeCmd.Result.Trim()}\n" +
                                $"   内存使用: {memoryCmd.Result.Trim()}");
                        }
                        else
                        {
                            return (false, "❌ 连接失败：无法建立SSH连接");
                        }
                    }
                }
                catch (SshAuthenticationException ex)
                {
                    return (false, $"❌ 认证失败：密钥文件无效或需要密码\n\n{ex.Message}");
                }
                catch (SshConnectionException ex)
                {
                    return (false, $"❌ 连接异常：{ex.Message}");
                }
                catch (Exception ex)
                {
                    return (false, $"❌ 连接失败：{ex.Message}");
                }
            });
        }

        private void ShowMessage(string title, string message, bool isSuccess)
        {
            ResultTitle.Text = title;
            ResultText.Text = message;

            // 根据成功/失败设置颜色
            ResultTitle.Foreground = isSuccess ?
                new SolidColorBrush(Color.FromRgb(46, 125, 50)) : // 绿色
                new SolidColorBrush(Color.FromRgb(211, 47, 47));  // 红色

            // 显示结果面板
            ResultPanel.Visibility = Visibility.Visible;
            var fadeIn = new DoubleAnimation
            {
                From = 0,
                To = 1,
                Duration = TimeSpan.FromSeconds(0.5)
            };
            ResultPanel.BeginAnimation(UIElement.OpacityProperty, fadeIn);
        }

        private void CloseResultButton_Click(object sender, RoutedEventArgs e)
        {
            var fadeOut = new DoubleAnimation
            {
                From = 1,
                To = 0,
                Duration = TimeSpan.FromSeconds(0.3)
            };

            fadeOut.Completed += (s, args) =>
            {
                ResultPanel.Visibility = Visibility.Collapsed;
            };

            ResultPanel.BeginAnimation(UIElement.OpacityProperty, fadeOut);
        }

        private async Task ShowLoading(bool show)
        {
            if (show)
            {
                DisableAllControls();
                LoadingGrid.Visibility = Visibility.Visible;
                var fadeIn = new DoubleAnimation
                {
                    To = 1,
                    Duration = TimeSpan.FromSeconds(0.3)
                };
                LoadingGrid.BeginAnimation(UIElement.OpacityProperty, fadeIn);

                var rotateAnimation = new DoubleAnimation
                {
                    From = 0,
                    To = 360,
                    Duration = TimeSpan.FromSeconds(1),
                    RepeatBehavior = RepeatBehavior.Forever
                };
                LoadingRotate.BeginAnimation(RotateTransform.AngleProperty, rotateAnimation);
            }
            else
            {
                var fadeOut = new DoubleAnimation
                {
                    To = 0,
                    Duration = TimeSpan.FromSeconds(0.3)
                };

                var tcs = new TaskCompletionSource<bool>();
                fadeOut.Completed += (s, e) =>
                {
                    LoadingGrid.Visibility = Visibility.Collapsed;
                    LoadingRotate.BeginAnimation(RotateTransform.AngleProperty, null);
                    tcs.SetResult(true);
                };

                LoadingGrid.BeginAnimation(UIElement.OpacityProperty, fadeOut);
                await tcs.Task;
                EnableAllControls();
            }
        }

        private void DisableAllControls()
        {
            ServerIpInput.IsEnabled = false;
            PortInput.IsEnabled = false;
            NoAuthRadio.IsEnabled = false;
            PasswordRadio.IsEnabled = false;
            KeyRadio.IsEnabled = false;
            PasswordInput.IsEnabled = false;
            KeySelectButton.IsEnabled = false;
            ConnectButton.IsEnabled = false;
        }

        private void EnableAllControls()
        {
            ServerIpInput.IsEnabled = true;
            PortInput.IsEnabled = true;
            NoAuthRadio.IsEnabled = true;
            PasswordRadio.IsEnabled = true;
            KeyRadio.IsEnabled = true;
            PasswordInput.IsEnabled = PasswordRadio.IsChecked == true;
            KeySelectButton.IsEnabled = KeyRadio.IsChecked == true;
            ConnectButton.IsEnabled = true;
        }
    }
}