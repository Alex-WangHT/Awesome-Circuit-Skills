# Awesome Circuit Skills

面向 Codex 的电路工程技能，覆盖电路架构规划、原理图绘制与器件库制作。

| Skill | 适用任务 |
|---|---|
| [circuit-architecture](skills/circuit-architecture/SKILL.md) | 根据需求文档划分模块、帮助选型，生成 PCB 设计前期的 Block Diagram、Power Tree 和逐信号 Pinlist。 |
| [circuit-schematic](skills/circuit-schematic/SKILL.md) | 绘制、整理和检查原理图；分图页、总线、去耦、外围阻容、接口保护及标识。 |
| [circuit-library](skills/circuit-library/SKILL.md) | 从 datasheet 建立符号、PCB 封装、3D 模型并关联工程库。 |

## 安装与使用

将所需的完整技能目录复制到 `$CODEX_HOME/skills/`；未设置 `CODEX_HOME` 时，使用 `~/.codex/skills/`。例如安装后的入口为 `~/.codex/skills/circuit-architecture/SKILL.md`。`circuit-architecture` 只有 `SKILL.md`，其余技能安装时须保留各自的 `references/` 和 `agents/`。各技能目录可以独立安装。

在 Codex 中使用 `$circuit-architecture`、`$circuit-schematic` 或 `$circuit-library`，并给出需求文档、目标工程、对象和任务范围。建议先由架构技能确定选型、供电、总线和引脚对应，再用原理图技能实现电气连接；涉及新器件库时使用器件库技能。

示例请求：

- “使用 $circuit-architecture，根据需求文档帮助选型，生成 Block Diagram、Power Tree 和逐信号 Pinlist，并列出尚未确认的器件引脚。”
- “使用 $circuit-schematic，只整理指定分图页，保留现有电气连接，导出 PDF 和图片并复查。”
- “使用 $circuit-library，根据完整料号的厂家资料建立符号、PCB 封装和 STEP 模型，关联到工程库。”

架构技能是纯文档指令，不附带生成脚本。Block Diagram、Power Tree 和 Pinlist 是 PCB 设计的前期资料；它们不是已完成布线的 PCB 文件或电气原理图。

## 规则与范围

完整原理图设计要求 Block Diagram、Power Tree、Pinlist 齐备且一致。用户明确限定页内排版或局部检查时，按其范围处理并记录未核验项。

每组去耦最多 7 颗、48 脚符号分区阈值等属于原理图技能的默认绘图约定，项目明确要求可以覆盖；器件引脚、尺寸及电气连接必须有资料依据。网表一致、ERC/DRC、图面检查及系统验证分别记录。架构技能应标出假设与待确认项；未经 datasheet 核实的物理引脚不得标记为已确认。

库中不包含具体开发板图纸、厂家 PDF 或第三方 CAD 文件；文中的外部资料链接保留原来源，引用资料的权利归各自所有者。

## 目录

```text
skills/
  circuit-architecture/
    SKILL.md
  circuit-schematic/
    SKILL.md
    agents/openai.yaml
    references/原理图绘制设计规则.md
    references/分图页-芯片去耦电容.md
    references/分图页-对外接口与ESD.md
    references/分图页-芯片外围小元件.md
  circuit-library/
    SKILL.md
    agents/openai.yaml
    references/器件工程库制作标准.md
```

`main` 保留稳定内容；新技能在 `develop` 分支开发，不合并到 `main`。
