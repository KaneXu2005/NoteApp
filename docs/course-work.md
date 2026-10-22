# 课程任务与复现入口

分阶段完成，提交目标仅为 **KaneXu2005/NoteApp 的 main**。不修改教师仓库。
课件没有上传：仓库保存自己的实现、分析、教学图像、实测摘要与复现脚本。

| 阶段 | 课程依据 | 成果 |
|---|---|---|
| 1 | Session 03 p30，Part 1–2 | [凯撒与 ECB/GCM](../labs/session03/README.md)、对比图和运行输出 |
| 2 | Session 03 p30，Part 3 | [评论列 AES-GCM](comment-encryption.md)，存量迁移和读写路径 |
| 3 | Class 4 内容页 13、20–21 | [CSV HMAC](export-integrity.md)，SHA-256/HMAC/RSA 演示 |
| 4 | Class 5 内容页 5、8–9 与在线 Lab 1 | [HTTPS 审计](https-audit.md)、证书、端口和真实抓包验证 |
| 5 | Class 5 内容页 15–18 与在线 Lab 2 | [密码审计](password-audit.md)、Argon2id 迁移、词表与计时 |
| 6 | Session 02 p33–34、Session 03 p31 | [Project 1](threat-model.md)：编号图、六类 STRIDE、L×I、前三项修复及 3 分钟提纲 |

Class 5 PDF 含逐步动画的重复页，表内“内容页”指投影片底部编号。
在线 Lab 2 的词表和六个示例账户与幻灯片示例不同，实测采用在线实验版本，报告明确注明。

## 在新的 clone 上启动

需要 Docker Compose 支持 `!reset` 与 `!override`（2.24.4+）。

```sh
python3 scripts/setup_secrets.py
scripts/generate_cert.sh
docker compose -p notesapp-course \
  -f docker-compose.yml -f docker-compose.lab.yml -f docker-compose.https.yml \
  up -d --build
curl --cacert nginx/certs/notesapp.crt https://localhost/login
```

访问 `https://localhost`。自签证书不是公开 CA 证书，浏览器默认不信任；
命令行通过 `--cacert` 明确验证本地证书，不需要把它加入全局信任或关闭校验。
账户沿用课程 README：alice、prof.turing、admin。仅使用课程测试密码。

保留 `.env` 与数据库的对应关系，单独备份密钥。已有数据库应先备份再迁移。
不要删除 `.env` 后重建随机密钥来处理错误，否则原有评语无法解密。
启动会迁移评语；密码只在成功登录时逐个升级，尚未登录的账户仍为旧存储。

推荐的 lab 覆盖配置不发布数据库、不挂载主机/socket、只监听本机。
原始 compose 保留教学配置；不要单独使用它部署公共服务。

## 测试

```sh
# 不需要数据库的回归测试：
python3 -m venv .venv
.venv/bin/pip install -r web/requirements.txt
.venv/bin/python -m unittest discover -s tests -v

# 实际 HTTPS 入口角色访问：
python3 scripts/smoke_https.py

# 只对专用教学数据库运行集成测试：
docker cp tests notesapp-course-web-1:/tmp/tests
docker exec -e NOTESAPP_TEST_DATABASE=1 notesapp-course-web-1 python /tmp/tests/integration_comments.py
docker exec -e NOTESAPP_TEST_DATABASE=1 notesapp-course-web-1 python /tmp/tests/integration_migration.py
docker exec -e NOTESAPP_TEST_DATABASE=1 notesapp-course-web-1 python /tmp/tests/integration_passwords.py
```

评论测试创建并清理专用记录；回滚测试临时改写两条种子评语并在 finally 中恢复。
密码测试保留 alice/admin 已迁移状态、清理临时测试账户。重复运行时 alice_was_legacy
可能为 false；首次运行的真实证据保存在 `docs/evidence/password-migration.json`。
图片实验额外依赖 `labs/session03/requirements.txt`；完整运行方法见其 README。
本次测试均为本机实际执行；没有将本地验证描述为 GitHub CI 结果。

## 实际验证记录

- 7 项单元测试通过：nonce、Unicode/NULL、认证失败、密文搬移、HMAC 改动、密码迁移/盐/重哈希。
- 60 条初始评语加密；重复迁移 0 行；错误密钥与后续损坏均验证事务回滚。
- 学生 dashboard/本人 API、教师页面/导出、管理员页面通过真实 HTTPS 访问，均 HTTP 200。
- 原始端口 8080 关闭、80 重定向、443 正常、nginx 配置检查通过。
- 课程合成账户词表破解及速度为真实测量，见两个审计报告。

## 提交范围和仍需本人完成的课堂事项

已完成实现与可复现分析。没有虚构小组讨论、预测答案、签署伦理章程或实际课堂展示。
原始 pcap 保存在本机 `docs/evidence/`，不上传含会话的原始抓包；Git 中只有摘要和指纹。
在线 Lab 1 要求的 Wireshark UI 截图需要本人打开这些真实 pcap 后截取，本次未伪造截图。
课程展示可直接使用 Project 1 中的提纲。所有风险评分是分析判断，可按小组讨论调整。

用户名拼接 SQL 按课件要求保留，弱 JWT、记录越权、XSS、CSRF、管理命令执行等也尚未修复。
本轮课程加密措施不构成生产安全保证，具体残余风险见 Project 1。
