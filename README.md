# Awesome Circuit Skills

面向 Codex 的中文电路工程技能，覆盖原理图绘制与器件库制作。由现有工程中的五份通用规范整理，保留去耦、晶振、符号分区、连接验证和导出图面复查要求。

| Skill | 适用任务 |
|---|---|
| [circuit-schematic](skills/circuit-schematic/SKILL.md) | 绘制、整理和检查原理图；分图页、总线、去耦、外围阻容、接口保护及标识。 |
| [circuit-library](skills/circuit-library/SKILL.md) | 从 datasheet 建立符号、PCB 封装、3D 模型并关联工程库。 |

## 安装与使用

将所需的完整技能目录复制到 `$CODEX_HOME/skills/`；未设置 `CODEX_HOME` 时，使用 `~/.codex/skills/`。例如安装后的入口为 `~/.codex/skills/circuit-schematic/SKILL.md`。不要只复制入口，须一并保留 `references/` 和 `agents/`。

在 Codex 中使用 `$circuit-schematic` 或 `$circuit-library`，并给出目标工程、对象和任务范围。两个技能默认允许按任务自动选择，也可独立安装。

示例请求：

- “使用 $circuit-schematic，只整理指定分图页，保留现有电气连接，导出 PDF 和图片并复查。”
- “使用 $circuit-library，根据完整料号的厂家资料建立符号、PCB 封装和 STEP 模型，关联到工程库。”

## 规则与范围

完整原理图设计要求 block diagram、powertree、pinlist 齐备且一致。用户明确限定页内排版或局部检查时，按其范围处理并记录未核验项。

每组去耦最多 7 颗、48 脚符号分区阈值等属于本技能的默认绘图约定，项目明确要求可以覆盖；器件引脚、尺寸及电气连接必须有资料依据。网表一致、ERC/DRC、图面检查及系统验证分别记录。

库中不包含具体开发板图纸、项目生成脚本、厂家 PDF 或第三方 CAD 文件；文中的外部资料链接保留原来源，引用资料的权利归各自所有者。

## 目录

```text
skills/
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
