# 参考资料 · Mira Bio 参考页结构

> 仅记录改版要用的客观信息。参考页：<https://www.framer.com/marketplace/templates/mira-bio/>
> 在线预览：<https://mirabio.framer.website/>（2026-11-10 访问）

## 页面组成（参考页 5 页 + 404）

| 页面 | 内容 |
|---|---|
| Overview | 需关注指标、生物学年龄、睡眠与恢复、今日计划、照护团队对话 |
| Biomarkers | 17 项指标列表 + 分类侧栏 + 状态筛选 + 右侧详情卡（趋势图） |
| Sleep | 睡眠阶段图、评分盘、就寝/起床、目标对照、4 项统计 |
| Plan | 3 个重点领域（进度环 + 清单 + 目标）、今日清单、补剂 |
| Care | 医生线程、预约卡（Day/Slot chip） |
| 404 | 暗色径向渐变卡 + 返回按钮 |

## 视觉 token（从在线页取的实测值）

| 用途 | 值 |
|---|---|
| 页面底色 | `#EFEFEE` |
| 卡片 | `#FFFFFF` / 内嵌卡 `#F7F7F5` / 轨道 `#ECECEA` |
| 主文字 | `#0F110F`；次级 `#3E3E3B` `#6B6B68` `#94948F` |
| 强调色（青柠） | `#D7F43A`；次级绿 `#8FD94E`；浅青柠底 `#F1F7DA` |
| 关注 / 沙色 | `#F6E7A8` |
| 偏低 / 浅赭 | `#F7DDD5` |
| 暗卡 | 橄榄绿 → 近黑径向渐变（顶亮右下暗） |
| 字体 | Geist（正文）/ Geist Mono（标签、数字） |
| 卡片圆角 | 约 28–32 px；胶囊按钮 999 px |

## 组件命名（参考页官方说明）

Header · Marker Row · Category Item · Status Chip · Check Row · Clinician Item ·
Day Chip · Slot Chip · booking buttons；官方另有 22 个文本样式、37 个颜色 token。

本项目预览在此基础上新增：**Chat Panel / Message Bubble / Prediction Card**。

## 交互（参考页）

- 点任一指标打开详情卡（含趋势图）
- 状态（Optimal/Watch/Low）× 分类组合筛选
- 每日清单可勾选
- 卡片与图表加载时入场动画
- 桌面 / 平板 / 手机三档；手机标签栏移到底部

## 本项目预览的映射

| 参考页 | 本项目 |
|---|---|
| 医生对话线程 | **本地模型聊天**（`#/care`），保留三栏骨架与气泡 |
| 预约卡 | 「模型复盘」占位卡（Day/Slot chip，无真实排期） |
| 生物学年龄 | 保留模块，标注示例（项目暂无估算模型） |
| 17 项指标 | 7 项接真实字段，10 项占位 |
| 趋势图 | 内联 SVG 现算（参考页是 CMS 图片） |
| 品牌 | 「腕上健康」，logo「腕」 |

## 可用命令

```powershell
start presentation\index.html      # 打开预览
Get-Content experiment\results.csv # 核对实验数字
```
