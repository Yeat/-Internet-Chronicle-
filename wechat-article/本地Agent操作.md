# 用本地 Cursor Agent 发到微信公众号

云端 Agent 登不了你的号。换成本机 Cursor Agent 后，它可以操作你电脑上的浏览器完成发布。

## 1. 先把稿子拿到本机

任选一种：

**A. 拉分支（推荐）**

```bash
git fetch origin cursor/wechat-article-talent-yesterday-00e6
git checkout cursor/wechat-article-talent-yesterday-00e6
```

**B. 只下发布包**

从仓库根目录下载 `wechat-local-publish.zip`，解压到任意文件夹。

## 2. 用 Cursor 打开该目录

打开包含 `wechat-article/` 的仓库，或解压后的发布包目录。确认能看到：

- `wechat-article/paste-to-wechat.html`
- `wechat-article/images/01-cover.jpg` … `05-two-futures.jpg`

## 3. 本机先登录公众号（重要）

浏览器打开 https://mp.weixin.qq.com ，扫码登录你的公众号。  
本地 Agent 可以帮你点页面，但**扫码这一步必须你自己完成**。

## 4. 把下面整段提示词发给本地 Agent

```text
请用本机浏览器，把微信公众号文章发到草稿箱（先不要正式群发）。

素材位置：
- 正文：wechat-article/paste-to-wechat.html
- 图片：wechat-article/images/01-cover.jpg 到 05-two-futures.jpg

发布信息：
- 标题：他把 DeepSeek 的核心算子写完，接着说了一句很丧的话
- 摘要：DeepSeek 工程师写完 V4.1 主 Attention 后发文：活大概还在，但手写算子那套最让他上瘾的干法正在过时。
- 作者：按账号默认即可

操作要求：
1. 打开 https://mp.weixin.qq.com ；若未登录，停下来让我扫码。
2. 进入「草稿箱」→「新的创作」→「文章」。
3. 填写标题、摘要；封面上传 images/01-cover.jpg。
4. 打开 paste-to-wechat.html，复制正文，粘贴进编辑器。
5. 若图片裂了或还是本地路径，按 01→05 顺序重新上传插入。
6. 点「预览」发到我微信；确认无误后「保存草稿」。
7. 未经我明确说「发表/群发」前，不要点发表或群发。
8. 做完后告诉我：草稿是否已保存、预览是否已发到手机。
```

## 5. 你需要配合的时刻

| 时刻 | 你做什么 |
| --- | --- |
| 出现登录二维码 | 手机扫码 |
| Agent 发预览到微信 | 手机打开看排版 |
| 确认无误要正式上线 | 再对 Agent 说：「可以发表」 |

## 常见问题

**Agent 说打不开浏览器 / 没有 computer use**  
用 Cursor Desktop 本地对话，并允许它使用电脑/浏览器相关权限；云端 Agent 做不了这一步。

**粘贴后格式乱、图全裂**  
让 Agent 改成：先贴纯文本，再按 `01`～`05` 手动插图；引用块用编辑器自带「引用」。

**只想存草稿，暂时不发**  
上面提示词默认就是「只存草稿」。要上线时另说一句即可。
