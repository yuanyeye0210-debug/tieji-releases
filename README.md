# 铁纪（Tieji）安装包下载

铁纪的公开下载地址。每次云端 CI 打完包，会自动把 IPA 和 `latest.json` 更新到这个仓库的 `main` 分支。App 内「关于 › 检查更新」读的就是这里的清单。

## 当前版本

见 [`latest.json`](./latest.json)。直接下载（把版本号换成清单里的 `latest`）：

`https://raw.githubusercontent.com/yuanyeye0210-debug/tieji-releases/main/Tieji-vX.Y.Z.ipa`

例如 1.4.1：

https://raw.githubusercontent.com/yuanyeye0210-debug/tieji-releases/main/Tieji-v1.4.1.ipa

校验：[`SHA256SUMS`](./SHA256SUMS)

## 安装

用 SideStore 或 Sideloadly 装到 iPhone。先下载 IPA 到「文件」，打开 LocalDevVPN 并连接，再打开 SideStore 点 + 选中这个 IPA。训练数据不会因为重装而丢失（导出备份仍然建议定期做）。

## 清单格式

`latest.json` 与课曜的 classday-releases 相同（`schema_version: 1`，`channels.ios`）。
