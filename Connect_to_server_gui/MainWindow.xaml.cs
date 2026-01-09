using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Animation;
using Renci.SshNet;
using Microsoft.Win32;

namespace Connect_to_server_gui
{
    public partial class MainWindow : Window
    {
        private SshClient _sshClient;
        private bool _isConnected = false;
        private string _selectedFolderPath = string.Empty;
        private string _currentServerPath = "/";

        private readonly Dictionary<string, List<string>> _suggestedPaths =
            new Dictionary<string, List<string>>
            {
                ["Linux"] = new List<string> { "/home/user/Familytree", "/root/Familytree", "/opt/Familytree" },
                ["Windows"] = new List<string> { @"C:\Familytree", @"D:\Familytree", @"C:\Program Files\Familytree" },
                ["macOS"] = new List<string> { "/Users/user/Familytree", "/Library/Familytree", "/Applications/Familytree" }
            };

        public MainWindow()
        {
            InitializeComponent();
            InitUI();
            BindEvents();
            AnimateStartup();
        }

        #region 初始化
        private void InitUI()
        {
            Dispatcher.Invoke(() =>
            {
                NoAuthRadio.IsChecked = true;
                LinuxRadio.IsChecked = true;
                ManualInputRadio.IsChecked = true;
                UpdateSuggestedPaths("Linux");
                SetWatermark(ServerIpInput, "用户名@服务器IP");
                PasswordInput.IsEnabled = false;
                KeySelectButton.IsEnabled = false;
                BrowseButton.IsEnabled = false;
                ContinueButton.IsEnabled = false;
                if (KeyFilePathText != null && string.IsNullOrEmpty(KeyFilePathText.Text))
                    KeyFilePathText.Text = "未选择文件";
            });
        }

        private void SetWatermark(TextBox tb, string watermark)
        {
            if (string.IsNullOrEmpty(tb.Text))
            {
                tb.Text = watermark;
                tb.Foreground = Brushes.Gray;
            }
            tb.GotFocus += (s, e) =>
            {
                if (tb.Text == watermark)
                {
                    tb.Text = "";
                    tb.Foreground = Brushes.Black;
                }
            };
            tb.LostFocus += (s, e) =>
            {
                if (string.IsNullOrEmpty(tb.Text))
                {
                    tb.Text = watermark;
                    tb.Foreground = Brushes.Gray;
                }
            };
        }

        private void BindEvents()
        {
            NoAuthRadio.Checked += AuthType_Checked;
            PasswordRadio.Checked += AuthType_Checked;
            KeyRadio.Checked += AuthType_Checked;

            LinuxRadio.Checked += OsRadio_Checked;
            WindowsRadio.Checked += OsRadio_Checked;
            MacRadio.Checked += OsRadio_Checked;

            ManualInputRadio.Checked += SelectMethod_Checked;
            BrowseServerRadio.Checked += SelectMethod_Checked;
            SuggestedPathRadio.Checked += SelectMethod_Checked;

            ConnectButton.Click += ConnectButton_Click;
            KeySelectButton.Click += KeySelectButton_Click;
            ValidatePathButton.Click += ValidatePathButton_Click;
            CreateFolderButton.Click += CreateFolderButton_Click;
            ContinueButton.Click += ContinueButton_Click;
            BrowseButton.Click += BrowseButton_Click;
            SelectFolderButton.Click += SelectFolderButton_Click;
            CancelBrowseButton.Click += CancelBrowseButton_Click;
            GoUpButton.Click += GoUpButton_Click;
        }
        #endregion

        #region 认证 & OS & 选择方式
        private void AuthType_Checked(object sender, RoutedEventArgs e)
        {
            Dispatcher.Invoke(() =>
            {
                PasswordInput.IsEnabled = PasswordRadio.IsChecked == true;
                KeySelectButton.IsEnabled = KeyRadio.IsChecked == true;
            });
        }

        private void OsRadio_Checked(object sender, RoutedEventArgs e)
        {
            if (LinuxRadio.IsChecked == true)
                UpdateSuggestedPaths("Linux");
            else if (WindowsRadio.IsChecked == true)
                UpdateSuggestedPaths("Windows");
            else if (MacRadio.IsChecked == true)
                UpdateSuggestedPaths("macOS");
        }

        private void SelectMethod_Checked(object sender, RoutedEventArgs e)
        {
            Dispatcher.Invoke(() =>
            {
                ManualPathInput.IsEnabled = ManualInputRadio.IsChecked == true;
                BrowseButton.IsEnabled = BrowseServerRadio.IsChecked == true && _isConnected;
                CurrentPathInput.IsEnabled = BrowseServerRadio.IsChecked == true;
            });
        }

        private void UpdateSuggestedPaths(string os)
        {
            Dispatcher.Invoke(() =>
            {
                if (SuggestedPathsPanel == null) return;
                SuggestedPathsPanel.Children.Clear();
                if (!_suggestedPaths.TryGetValue(os, out var list)) return;
                foreach (var p in list)
                {
                    var btn = new Button
                    {
                        Content = p,
                        Width = 400,
                        Height = 35,
                        Margin = new Thickness(0, 5, 0, 5),
                        HorizontalContentAlignment = HorizontalAlignment.Left,
                        Padding = new Thickness(10, 0, 0, 0),
                        Background = Brushes.White,
                        BorderBrush = Brushes.LightGray,
                        BorderThickness = new Thickness(1)
                    };
                    btn.Click += (s, e) =>
                    {
                        Dispatcher.Invoke(() =>
                        {
                            ManualPathInput.Text = p;
                            _selectedFolderPath = p;
                        });
                    };
                    SuggestedPathsPanel.Children.Add(btn);
                }
            });
        }
        #endregion

        #region SSH 连接
        private async void ConnectButton_Click(object sender, RoutedEventArgs e)
        {
            if (Dispatcher.Invoke(() => ServerIpInput.Text == "用户名@服务器IP") ||
                Dispatcher.Invoke(() => !ServerIpInput.Text.Contains('@')))
            {
                MessageBox.Show("请输入正确格式：用户名@IP", "错误");
                return;
            }

            if (!int.TryParse(Dispatcher.Invoke(() => PortInput.Text), out int port) || port <= 0 || port > 65535)
            {
                MessageBox.Show("端口无效（1-65535）", "错误");
                return;
            }

            var serverText = Dispatcher.Invoke(() => ServerIpInput.Text);
            var ss = serverText.Split('@');
            string user = ss[0], host = ss[1];

            ShowLoading("正在连接...");
            try
            {
                await Task.Run(() =>
                {
                    bool isNoAuth = Dispatcher.Invoke(() => NoAuthRadio.IsChecked == true);
                    bool isPassword = Dispatcher.Invoke(() => PasswordRadio.IsChecked == true);
                    bool isKey = Dispatcher.Invoke(() => KeyRadio.IsChecked == true);

                    if (isNoAuth)
                        _sshClient = new SshClient(host, port, user);
                    else if (isPassword)
                    {
                        var password = Dispatcher.Invoke(() => PasswordInput.Password);
                        _sshClient = new SshClient(host, port, user, password);
                    }
                    else if (isKey)
                    {
                        var keyPath = Dispatcher.Invoke(() => KeyFilePathText.Text);
                        if (keyPath == "未选择文件")
                            throw new Exception("请选择私钥文件");
                        var pk = new PrivateKeyFile(keyPath);
                        _sshClient = new SshClient(host, port, user, new[] { pk });
                    }
                    _sshClient.Connect();
                });

                _isConnected = true;
                HideLoading();

                Dispatcher.Invoke(() =>
                {
                    ServerInfoText.Text = $"已连接到：{host}:{port}\n用户名：{user}\nSSH版本：SSH-2.0";
                    AnimatePanelSwitch(ConnectionPanel, FolderPanel);
                });
            }
            catch (Exception ex)
            {
                HideLoading();
                MessageBox.Show(ex.Message, "连接失败");
            }
        }

        private void KeySelectButton_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Filter = "私钥文件 (*.pem;*.ppk)|*.pem;*.ppk|所有文件 (*.*)|*.*",
                Title = "选择SSH私钥文件"
            };
            if (dlg.ShowDialog() == true)
                Dispatcher.Invoke(() => KeyFilePathText.Text = dlg.FileName);
        }
        #endregion

        #region 目录浏览
        private async void BrowseButton_Click(object sender, RoutedEventArgs e)
        {
            if (!_isConnected)
            {
                MessageBox.Show("请先连接服务器", "错误");
                return;
            }

            await Dispatcher.InvokeAsync(async () =>
            {
                DirectoryBrowserGrid.Visibility = Visibility.Visible;
                var fade = new DoubleAnimation(0, 1, TimeSpan.FromSeconds(0.3));
                DirectoryBrowserGrid.BeginAnimation(OpacityProperty, fade);
                await LoadDirectoryContents(_currentServerPath);
            });
        }

        private async Task LoadDirectoryContents(string path)
        {
            // 在 UI 线程初始化
            await Dispatcher.InvokeAsync(async () =>
            {
                ShowLoading("正在加载目录...");
                BrowserDirectoryListPanel?.Children.Clear();
                if (BrowserPathInput != null) BrowserPathInput.Text = path;

                try
                {
                    // 在后台线程执行 SSH 命令
                    var (result, error) = await Task.Run(() =>
                    {
                        try
                        {
                            if (_sshClient == null || !_sshClient.IsConnected)
                                throw new Exception("SSH连接已断开");

                            // 使用更简单的命令来避免编码问题
                            var cmd = _sshClient.CreateCommand($"ls -la \"{EscapePath(path)}\" 2>&1");
                            var res = cmd.Execute();
                            return (res, cmd.Error);
                        }
                        catch (Exception ex)
                        {
                            return (string.Empty, ex.Message);
                        }
                    });

                    if (!string.IsNullOrEmpty(error) && error.Contains("No such file"))
                    {
                        // 目录不存在，创建它
                        await TryCreateDirectory(path);
                        return;
                    }

                    if (!string.IsNullOrEmpty(error))
                    {
                        throw new Exception($"无法访问目录: {error}");
                    }

                    // 解析结果并在 UI 线程更新
                    ProcessDirectoryResult(result, path);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"加载目录失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                }
                finally
                {
                    HideLoading();
                }
            });
        }

        private async Task TryCreateDirectory(string path)
        {
            // 移除 await，MessageBox.Show 是同步方法
            var result = MessageBox.Show($"目录 '{path}' 不存在，是否创建？", "确认",
                MessageBoxButton.YesNo, MessageBoxImage.Question);

            if (result != MessageBoxResult.Yes) return;

            ShowLoading("正在创建目录...");
            try
            {
                var success = await Task.Run(() =>
                {
                    var cmd = _sshClient.CreateCommand($"mkdir -p \"{EscapePath(path)}\"");
                    cmd.Execute();
                    return cmd.ExitStatus == 0;
                });

                if (success)
                {
                    // 重新加载目录
                    await LoadDirectoryContents(path);
                }
                else
                {
                    MessageBox.Show("创建目录失败", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"创建目录失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                HideLoading();
            }
        }

        private string EscapePath(string path)
        {
            // 转义路径中的特殊字符
            return path.Replace("\"", "\\\"");
        }

        private void ProcessDirectoryResult(string result, string path)
        {
            if (BrowserDirectoryListPanel == null) return;

            var lines = result.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);

            // 如果没有内容（空目录）
            if (lines.Length == 0)
            {
                var emptyText = new TextBlock
                {
                    Text = "（空目录）",
                    FontSize = 14,
                    Foreground = Brushes.Gray,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    Margin = new Thickness(10)
                };
                BrowserDirectoryListPanel.Children.Add(emptyText);
                return;
            }

            foreach (var line in lines)
            {
                if (string.IsNullOrWhiteSpace(line) || line.StartsWith("total")) continue;

                var parts = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length < 9) continue;

                bool isDir = parts[0].StartsWith("d");
                string name = parts[8];

                // 跳过 . 和 ..
                if (name == "." || name == "..") continue;

                // 处理长文件名（可能包含空格）
                if (parts.Length > 9)
                {
                    name = string.Join(" ", parts, 8, parts.Length - 8);
                }

                string full = path == "/" ? $"/{name}" : $"{path}/{name}";

                var sp = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    Margin = new Thickness(5),
                    Cursor = System.Windows.Input.Cursors.Hand,
                    ToolTip = $"类型: {(isDir ? "文件夹" : "文件")}\n路径: {full}"
                };

                var icon = new TextBlock
                {
                    Text = isDir ? "📁" : "📄",
                    FontSize = 16,
                    Margin = new Thickness(0, 0, 10, 0),
                    VerticalAlignment = VerticalAlignment.Center
                };

                var txt = new TextBlock
                {
                    Text = name,
                    FontSize = 14,
                    VerticalAlignment = VerticalAlignment.Center,
                    Foreground = isDir ? Brushes.DarkBlue : Brushes.Black,
                    TextWrapping = TextWrapping.Wrap
                };

                sp.Children.Add(icon);
                sp.Children.Add(txt);

                sp.MouseLeftButtonUp += async (s, e) =>
                {
                    if (isDir)
                    {
                        _currentServerPath = full;
                        await LoadDirectoryContents(full);
                    }
                };

                BrowserDirectoryListPanel.Children.Add(sp);
            }
        }

        private async void GoUpButton_Click(object sender, RoutedEventArgs e)
        {
            if (_currentServerPath == "/") return;
            var parent = Path.GetDirectoryName(_currentServerPath)?.Replace('\\', '/') ?? "/";
            _currentServerPath = parent;
            await LoadDirectoryContents(_currentServerPath);
        }

        private void SelectFolderButton_Click(object sender, RoutedEventArgs e)
        {
            Dispatcher.Invoke(() =>
            {
                _selectedFolderPath = _currentServerPath;
                ManualPathInput.Text = _currentServerPath;
                CurrentPathInput.Text = _currentServerPath;
                var fade = new DoubleAnimation(1, 0, TimeSpan.FromSeconds(0.3));
                fade.Completed += (s, _) => DirectoryBrowserGrid.Visibility = Visibility.Collapsed;
                DirectoryBrowserGrid.BeginAnimation(OpacityProperty, fade);
            });
        }

        private void CancelBrowseButton_Click(object sender, RoutedEventArgs e)
        {
            Dispatcher.Invoke(() =>
            {
                var fade = new DoubleAnimation(1, 0, TimeSpan.FromSeconds(0.3));
                fade.Completed += (s, _) => DirectoryBrowserGrid.Visibility = Visibility.Collapsed;
                DirectoryBrowserGrid.BeginAnimation(OpacityProperty, fade);
            });
        }
        #endregion

        #region 路径验证/创建/进入
        private async void ValidatePathButton_Click(object sender, RoutedEventArgs e)
        {
            if (!_isConnected)
            {
                MessageBox.Show("请先连接服务器");
                return;
            }

            string path = await Dispatcher.InvokeAsync(GetSelectedPath);
            if (string.IsNullOrEmpty(path))
            {
                MessageBox.Show("请输入或选择路径");
                return;
            }

            ShowLoading("正在验证...");
            try
            {
                bool ok = await Task.Run(() =>
                {
                    // 使用更简单的命令来验证目录是否存在
                    var cmd = _sshClient.CreateCommand($"[ -d \"{EscapePath(path)}\" ] && echo 'exists'");
                    var result = cmd.Execute().Trim().ToLower();
                    return result == "exists";
                });

                await Dispatcher.InvokeAsync(() =>
                {
                    HideLoading();
                    ValidationResultBorder.Visibility = Visibility.Visible;
                    if (ok)
                    {
                        ValidationResultTitle.Text = "✅ 路径有效";
                        ValidationResultTitle.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#2E7D32"));
                        ValidationResultText.Text = $"路径 {path} 存在且可访问";
                        ContinueButton.IsEnabled = true;
                        _selectedFolderPath = path;
                    }
                    else
                    {
                        ValidationResultTitle.Text = "❌ 路径无效";
                        ValidationResultTitle.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#C62828"));
                        ValidationResultText.Text = $"路径 {path} 不存在或无访问权限";
                        ContinueButton.IsEnabled = false;
                    }
                });
            }
            catch (Exception ex)
            {
                HideLoading();
                MessageBox.Show($"验证失败: {ex.Message}", "错误");
            }
        }

        private async void CreateFolderButton_Click(object sender, RoutedEventArgs e)
        {
            if (!_isConnected) return;

            string path = await Dispatcher.InvokeAsync(GetSelectedPath);
            if (string.IsNullOrEmpty(path))
            {
                MessageBox.Show("请输入要创建的文件夹路径");
                return;
            }

            // 移除 await，MessageBox.Show 是同步方法
            if (MessageBox.Show($"确定创建文件夹：{path} 吗？", "确认", MessageBoxButton.YesNo) != MessageBoxResult.Yes)
                return;

            ShowLoading("正在创建...");
            try
            {
                bool ok = await Task.Run(() =>
                {
                    var cmd = _sshClient.CreateCommand($"mkdir -p \"{EscapePath(path)}\"");
                    cmd.Execute();
                    return cmd.ExitStatus == 0;
                });

                HideLoading();
                if (ok)
                {
                    MessageBox.Show("创建成功");
                    // 重新验证路径
                    ValidatePathButton_Click(sender, e);
                }
                else
                {
                    MessageBox.Show("创建失败");
                }
            }
            catch (Exception ex)
            {
                HideLoading();
                MessageBox.Show($"创建失败: {ex.Message}", "错误");
            }
        }

        private void ContinueButton_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_selectedFolderPath) || !_isConnected)
            {
                MessageBox.Show("请先验证有效路径");
                return;
            }
            MessageBox.Show($"成功进入族谱系统！\n服务器路径：{_selectedFolderPath}", "成功");
            // TODO: 打开主窗口
        }

        private string GetSelectedPath()
        {
            if (ManualInputRadio.IsChecked == true)
                return ManualPathInput.Text.Trim();
            if (BrowseServerRadio.IsChecked == true)
                return CurrentPathInput.Text.Trim();
            if (SuggestedPathRadio.IsChecked == true)
                return ManualPathInput.Text.Trim();
            return string.Empty;
        }
        #endregion

        #region 动画 & 加载
        private void AnimateStartup()
        {
            Dispatcher.Invoke(() =>
            {
                if (WelcomeText == null) return;
                var wFade = new DoubleAnimation(0, 1, TimeSpan.FromSeconds(1.5)) { EasingFunction = new QuadraticEase() };
                WelcomeText.BeginAnimation(OpacityProperty, wFade);

                Task.Delay(1000).ContinueWith(_ =>
                {
                    Dispatcher.Invoke(() =>
                    {
                        if (ConnectionPanel == null) return;
                        ConnectionPanel.Visibility = Visibility.Visible;
                        var pFade = new DoubleAnimation(0, 1, TimeSpan.FromSeconds(1)) { EasingFunction = new QuadraticEase() };
                        ConnectionPanel.BeginAnimation(OpacityProperty, pFade);
                    });
                });
            });
        }

        private void ShowLoading(string txt = "正在加载...")
        {
            Dispatcher.Invoke(() =>
            {
                if (LoadingGrid == null || LoadingText == null || LoadingRotate == null) return;
                LoadingGrid.Visibility = Visibility.Visible;
                LoadingText.Text = txt;
                LoadingGrid.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromSeconds(0.3)));
                LoadingRotate.BeginAnimation(RotateTransform.AngleProperty,
                    new DoubleAnimation(0, 360, TimeSpan.FromSeconds(1)) { RepeatBehavior = RepeatBehavior.Forever });
            });
        }

        private void HideLoading()
        {
            Dispatcher.Invoke(() =>
            {
                if (LoadingGrid == null) return;
                var fade = new DoubleAnimation(1, 0, TimeSpan.FromSeconds(0.3));
                fade.Completed += (s, e) => { LoadingGrid.Visibility = Visibility.Collapsed; };
                LoadingGrid.BeginAnimation(OpacityProperty, fade);
            });
        }

        private void AnimatePanelSwitch(UIElement hide, UIElement show)
        {
            Dispatcher.Invoke(() =>
            {
                var hideAnim = new DoubleAnimation(1, 0, TimeSpan.FromSeconds(0.5));
                hideAnim.Completed += (s, e) =>
                {
                    hide.Visibility = Visibility.Collapsed;
                    show.Visibility = Visibility.Visible;
                    show.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromSeconds(0.5)));
                };
                hide.BeginAnimation(OpacityProperty, hideAnim);
            });
        }
        #endregion

        #region 清理
        protected override void OnClosing(System.ComponentModel.CancelEventArgs e)
        {
            base.OnClosing(e);
            if (_sshClient != null && _sshClient.IsConnected)
            {
                _sshClient.Disconnect();
                _sshClient.Dispose();
            }
        }
        #endregion
    }
}