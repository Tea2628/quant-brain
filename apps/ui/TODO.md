# UI 最小联调 TODO（v0.1）
## 目标
完成“查看→提案→审批→干跑→时间线”的可演示闭环（只读 + 干跑）。

## 任务清单
1) 提案卡片：映射 Proposal 字段（symbol/side/size/entry/tp/sl/tif/valid_until/rationale/risks/tags），展示 gaps 时的缺口提示。
2) 审批对话框：dry-1 / dry-2，拒绝必须填写 reason；调用 /api/proposals/{id}/approve。
3) 时间线：订阅 /ws/events，按 trace_id 聚合展示 proposal/risk/approval/execution。
4) 请求封装：统一错误码与三态（loading/empty/error）；取消/重试。
5) WS 重连：指数退避；断线提示。
6) 配置化：BFF 基址、CORS 白名单、主题 token。
7) 用例验证：对齐“文件库/测试/测试-干跑闭环与事件.md”12 条用例。

## 验收（DoD）
- 关键路径可演示；事件顺序正确；拒绝路径与缺口提示可复现。
