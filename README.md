# CSE594 作业 3 说明（中文）

本项目实现了两种实验条件：
- Baseline（无 AI 建议）
- With AI（有 AI 建议）

后端使用 SQLite 记录参与者与 trial 结果，并可导出 CSV 供统计分析。

## 1) 本地运行
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

设置环境变量：
```powershell
$env:FLASK_SECRET_KEY="replace_with_random_secret"
$env:ADMIN_TOKEN="replace_with_secure_admin_token"
$env:TRIALS_PER_PARTICIPANT="6"
$env:RUNTIME_DATA_DIR="data"
$env:REQUIRE_REAL_MTURK="0"
```

说明：
- `REQUIRE_REAL_MTURK=0`：允许本地/直链测试。
- `REQUIRE_REAL_MTURK=1`：仅允许从已接受的 MTurk 任务进入（必须有真实 `workerId`、`assignmentId`、`turkSubmitTo`），可防止非 MTurk 数据混入。

启动：
```powershell
python app/app.py
```

访问：
- 首页：`http://127.0.0.1:5000`
- 开始页：`http://127.0.0.1:5000/start`

## 2) MTurk 入口链接
- Baseline：`https://YOUR-APP-DOMAIN/mturk/baseline`
- With AI：`https://YOUR-APP-DOMAIN/mturk/with_ai`

说明：
- MTurk 会自动带上 `workerId`、`assignmentId`、`hitId`、`turkSubmitTo`。
- 系统会生成有含义的 survey code（带条件前缀 + 哈希片段），可用于回查。
- Worker 在 MTurk 页面手动粘贴 survey code 提交即可。

## 3) 数据导出
导出状态（JSON）：
`http://127.0.0.1:5000/admin/export?token=YOUR_ADMIN_TOKEN`

直接下载 CSV：
`http://127.0.0.1:5000/admin/export.csv?token=YOUR_ADMIN_TOKEN`

校验 survey code：
`http://127.0.0.1:5000/admin/verify_code?token=YOUR_ADMIN_TOKEN&survey_code=CODE_FROM_MTURK`

按 MTurk 提交信息做严格核验（推荐审核时使用）：
`http://127.0.0.1:5000/admin/check_submission?token=YOUR_ADMIN_TOKEN&survey_code=CODE_FROM_MTURK&assignment_id=ASSIGNMENT_ID_FROM_MTURK`

如果你也有 workerId，可进一步校验：
`http://127.0.0.1:5000/admin/check_submission?token=YOUR_ADMIN_TOKEN&survey_code=CODE_FROM_MTURK&assignment_id=ASSIGNMENT_ID_FROM_MTURK&worker_id=WORKER_ID_FROM_MTURK`

审核建议：
- 返回 `valid=true`：可批准。
- 返回 `valid=false`：通常为乱填 code、assignment 不匹配或未完成全部 trial，可拒绝并备注原因。

清空全部实验数据（仅用于 Sandbox 重测）：
```powershell
Invoke-WebRequest -Method Post "http://127.0.0.1:5000/admin/reset?token=YOUR_ADMIN_TOKEN&confirm=RESET"
```

## 4) Render 部署注意事项
- 本仓库 `render.yaml` 已配置 `RUNTIME_DATA_DIR=/var/data`。
- 运行时数据（`study.db` 与 `responses_export.csv`）写入 Render 挂载磁盘。
- `data/trials.csv` 作为只读题库保留在仓库中。
- 线上完成的 MTurk 数据应从线上导出接口获取，不会自动写回你本地电脑文件。

## 5) 分析脚本
```powershell
python analysis/analyze.py --input data/responses_export.csv --outdir analysis/analysis_output
```

## 6) 提交文件
- 最终提交说明：`submission_materials/FINAL_SUBMISSION.md`
