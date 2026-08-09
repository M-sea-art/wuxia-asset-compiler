# Codex × Wuxia Asset Compiler：Skills / Plugin 集成说明

> **定位：Codex 是 Wuxia Asset Compiler 的工程代理、工作流执行者和 Skill 宿主，不是几何生成真值本身。**

Wuxia Asset Compiler 的核心理念是把 AI 的自由度放在“理解、规划、工程迭代”层，把几何真值留给确定性合同、Factory、Blender 和验证器。

Codex 很适合承担这套系统的**工程代理层**：它可以读懂仓库、遵循 `AGENTS.md`、运行测试、修改 Factory、实现 Template Gap、检查 CI，并通过可复用 Skills 固化工作流。

本项目未来应优先被组织成 **Codex Skills / Plugin 可调用的资产编译能力**，而不是给 Codex 一个无限制的 Blender Python 入口。

---

## 一、为什么 Codex 适合这个项目

OpenAI 将 Codex 定位为软件工程 Agent，可以围绕仓库完成代码理解、修改、测试和交付任务。OpenAI 也支持用 `AGENTS.md` 给 Codex 提供持续的项目上下文和工程规范。

本项目恰好需要一种能够长期维护“资产编译器本身”的 Agent：

```text
发现参考图差距
      ↓
判断：参数问题 / Template Gap
      ↓
如果是参数问题
  → 调用已有 Skill / CLI 修复

如果是能力缺口
  → Codex 阅读项目规则
  → 实现新的 Macro / Factory
  → 增加测试
  → 跑 Blender smoke CI
  → 提交 PR
      ↓
编译器永久获得新能力
```

因此，Codex 的价值不在于“直接生成更多 mesh”，而在于：

> **让每一次视觉失败都能被转化成一次可测试、可审查、可复用的工程能力升级。**

---

## 二、Skills、Plugins 和本项目的关系

OpenAI Skills 是可复用工作流，可以包含说明、示例和代码，用于让 Codex 更稳定地执行重复任务。

Plugin 可以把一组 Skills 与所需的外部应用能力一起打包，形成面向某一工作流的可安装能力集合。

对 Wuxia Asset Compiler 来说，可以理解为：

```text
Wuxia Asset Compiler Plugin
│
├─ Skill: analyze-reference
├─ Skill: resolve-scene-spec
├─ Skill: compile-blender-asset
├─ Skill: visual-qa
├─ Skill: repair-asset
├─ Skill: implement-template-gap
├─ Skill: validate-glb
└─ Skill: godot-import-smoke

可选外部能力：
├─ GitHub / repository access
├─ Blender MCP / DCC bridge
└─ 游戏引擎或 CI 集成
```

Plugin 是“能力包”，Skill 是“可复用工作流”。

本项目不应该把所有内容塞进一个巨大 Skill。更适合拆成若干职责明确、可以组合的小 Skill。

---

## 三、Codex 在系统中的职责

### Codex 应该负责

#### 1. 操作编译器工作流

例如：

```text
reference analysis
→ resolve_reference.py
→ build_asset.py
→ Visual QA
→ apply_visual_review.py
→ rebuild
→ validation
```

Codex 应调用稳定 CLI、Macro 或 MCP 工具，而不是每次重新发明执行方式。

#### 2. 实现 Template Gap

当 Visual QA 输出：

```text
template_gap:
  vertical_shelving
```

Codex 可以：

1. 阅读现有 `prop_macros.py`；
2. 设计一个可复用 `add_tall_storage()` Macro；
3. 接入多个 Room Factory；
4. 增加 CI 门槛；
5. 运行 Blender smoke；
6. 提交可审查 PR。

这比让视觉 Agent 当场写一段临时 `bpy` 更符合项目目标。

#### 3. 维护合同和测试

Codex 可以负责：

- JSON Schema 演进；
- Scene Spec 契约测试；
- Resolver 回归；
- Visual QA 合同测试；
- Blender smoke；
- GLB / Godot 导入测试；
- 许可证和依赖检查。

#### 4. 把 GitHub Issue 变成工程改进

Visual QA 的能力缺口可以直接形成 Issue。

Codex 可以按 Issue 执行：

```text
Issue
→ 读取 AGENTS.md
→ 分析相关 Factory
→ 修改代码
→ 跑测试
→ 输出 PR
```

这样 Template Gap backlog 就可以成为“资产编译器能力树”。

---

## 四、Codex 不应该负责

### 1. 不应获得无限制的 Blender 几何权力

正常工作流中不应是：

```text
Codex
→ 自由生成 2000 行 bpy
→ 直接修改场景
→ 导出 GLB
```

而应该是：

```text
Codex
→ 选择 Skill
→ 调用高层 Compiler / Factory 操作
→ Blender 执行确定性代码
→ Validator 验收
```

### 2. 不应绕过 Scene Spec

任何 AI 驱动的资产变更都应尽量能够被表达、记录和重放。

如果某个变化无法进入 Spec / Macro / Factory，它通常意味着我们还缺一个正式能力，而不是应该绕开架构。

### 3. 不应把 Visual QA 当成几何真值

Codex 可以根据 Visual QA 决定下一步工程任务，但最终资产是否成立，仍由：

- Schema；
- 几何测量；
- topology validation；
- export validation；
- engine import test；

决定。

---

## 五、推荐的 Skill 拆分

OpenAI 对 Skills 的设计建议强调“小而可组合”。因此建议从以下 Skill 集开始，而不是做一个 `do-everything-wuxia-3d`。

### Skill 1：`wuxia-reference-analysis`

职责：

- 分析参考图；
- 输出合法 `reference_analysis.json`；
- 提供 confidence + evidence；
- 不生成 Blender 代码。

输出：

```text
reference_analysis.json
```

---

### Skill 2：`wuxia-resolve-spec`

职责：

- 调用确定性 Resolver；
- 输出 Scene Spec；
- 报告接受 / 拒绝的视觉估计；
- 不静默篡改越界值。

调用：

```text
tools/resolve_reference.py
```

---

### Skill 3：`wuxia-compile-asset`

职责：

- 调用 Blender 编译；
- 生成 GLB；
- 输出 canonical preview；
- 输出四方向 QA views；
- 输出 validation report。

调用：

```text
blender/build_asset.py
```

---

### Skill 4：`wuxia-visual-qa`

职责：

- 比较参考图与生成图；
- 给 composition / identity / density / lighting / style 等评分；
- 区分 parameter-fixable 和 template-gap；
- 只输出受约束 Visual Review。

---

### Skill 5：`wuxia-repair-asset`

职责：

- 应用有界 Visual QA patch；
- 每个 patch 都重新过 Scene Spec 合同；
- 无效修改自动拒绝 / 回滚；
- 重新编译并比较。

调用：

```text
tools/apply_visual_review.py
```

---

### Skill 6：`wuxia-template-gap-engineer`

这是 Codex 最有价值的 Skill 之一。

职责：

```text
Template Gap
→ 查找正确抽象层
→ Primitive / Macro / Factory / Style DNA
→ 实现
→ 添加测试
→ Blender smoke
→ PR
```

关键原则：

> 新能力必须尽可能复用到多个资产，而不是只修当前截图。

---

### Skill 7：`wuxia-asset-validator`

职责：

- 运行几何验证；
- GLB 验证；
- triangle / mesh budget；
- transform / pivot；
- UV / material；
- collision；
- 输出是否可交付。

---

### Skill 8：`wuxia-godot-import-smoke`

职责：

- 将产物导入 Godot 测试项目；
- 验证比例、材质、节点结构、碰撞和运行时加载；
- 输出引擎侧验收报告。

环境编译成功不等于游戏资产成功，这个 Skill 应成为最终门槛之一。

---

## 六、Plugin 的推荐组织方式

未来可考虑组织为：

```text
wuxia-asset-compiler-plugin/
│
├─ skills/
│  ├─ reference-analysis/
│  │  └─ SKILL.md
│  ├─ resolve-spec/
│  │  └─ SKILL.md
│  ├─ compile-asset/
│  │  └─ SKILL.md
│  ├─ visual-qa/
│  │  └─ SKILL.md
│  ├─ repair-asset/
│  │  └─ SKILL.md
│  ├─ template-gap-engineer/
│  │  └─ SKILL.md
│  └─ validate-asset/
│     └─ SKILL.md
│
├─ optional integrations
│  ├─ GitHub
│  ├─ Blender MCP
│  └─ Godot / CI bridge
│
└─ project repo
   └─ AGENTS.md
```

其中：

- `AGENTS.md` 保存**项目长期原则**；
- Skills 保存**某类任务怎么做**；
- Plugin 保存**一整套工作流需要哪些能力**；
- MCP / Apps 提供**连接外部工具的执行通道**；
- Compiler / Blender 代码保存**几何和执行真值**。

这四层不应混为一体。

---

## 七、AGENTS.md 与 Skills 的分工

### `AGENTS.md`

适合写：

- 项目宗旨；
- 代码结构；
- 权限边界；
- 测试要求；
- Factory 设计原则；
- Template Gap 规则；
- PR / CI 纪律。

它回答：

> **“在这个仓库里做任何事，必须遵守什么？”**

### Skill

适合写：

- 某项工作何时触发；
- 输入是什么；
- 具体执行步骤；
- 调用哪些脚本；
- 如何判断成功；
- 失败时如何退出。

它回答：

> **“这类任务具体应该怎么完成？”**

因此不要把整个项目手册复制到每个 Skill 里。

---

## 八、Skill 的设计原则

### 1. 小而可组合

优先：

```text
Analyze
Resolve
Compile
Review
Repair
Validate
```

而不是：

```text
MakePerfectWuxiaGameWorld.skill
```

### 2. 高层语义优先

Skill 应调用：

```text
compile_wuxia_asset
apply_visual_repair
implement_template_gap
validate_asset
```

而不是暴露：

```text
move_vertex
extrude_face
run_arbitrary_bpy
```

### 3. 每个 Skill 必须有停止条件

例如：

- Spec 不合法 → 停止；
- Template Gap → 不继续乱调参数；
- Validation fail → 不导出“成功”；
- CI 不绿 → 不宣称完成。

### 4. Skill 不能提高模型权限边界

Skill 应该让工作流**更稳定**，而不是成为绕过 Compiler Contract 的后门。

### 5. 技能输出应可审计

重要决策需要留下：

- 输入；
- 参数 proposal；
- confidence；
- accepted / rejected；
- validation report；
- template gap；
- CI / PR 结果。

---

## 九、Codex + Blender MCP 的正确关系

未来接 Blender MCP 时，推荐：

```text
Codex Skill
      ↓
高层 MCP Tool
      ↓
Compiler / Macro / Factory
      ↓
Blender
```

而不是：

```text
Codex
      ↓
execute_arbitrary_python
      ↓
Blender
```

推荐的 MCP 操作应接近：

```text
compile_scene_spec
render_qa_views
validate_asset
export_glb
inspect_scene_metrics
```

或者更高层：

```text
build_wuxia_asset
repair_wuxia_asset
implement_factory_macro
```

Raw Python 可以保留给工程调试，但不应成为正常生产 Agent 的默认接口。

---

## 十、Codex 在长期愿景中的角色

长期架构可以理解成：

```text
                 人 / 美术 / 设计
                       ↓
                  Reference
                       ↓
                Vision / VLM
                       ↓
                Asset Compiler
                       ↓
                     Blender
                       ↓
                      GLB

Codex 横跨的是“工程生命周期”：

Reference QA
    ↓
发现 Compiler 缺什么
    ↓
Codex + Skills
    ↓
修改 Compiler
    ↓
测试 / CI / PR
    ↓
Compiler 能力永久增长
```

因此 Codex 的目标不是替代 Blender。

它更接近：

> **一个持续维护和扩展“世界生成语法”的 AI 工程师。**

---

## 十一、官方 OpenAI 参考

以下文档用于本项目对 Codex / Skills / Plugins 的定位说明：

- [Skills in ChatGPT - OpenAI Help Center](https://help.openai.com/en/articles/20001066)
- [Plugins in ChatGPT and Codex - OpenAI Help Center](https://help.openai.com/en/articles/20001256-plugins-in-codex)
- [Codex - OpenAI](https://openai.com/codex/)
- [How OpenAI uses Codex - OpenAI](https://openai.com/business/guides-and-resources/how-openai-uses-codex/)
- [Introducing Codex - OpenAI](https://openai.com/index/introducing-codex/)
- [Using skills - OpenAI Academy](https://openai.com/academy/skills/)

这些官方资料说明了几项与本项目直接相关的能力：

1. Skills 用于封装可重复、可共享的工作流；
2. Codex 支持 Skills，并可用它们固化团队标准和工作方式；
3. Plugins 可以打包面向特定工作流的 Skills 和连接能力；
4. `AGENTS.md` 可以向 Codex 提供持久的仓库级上下文与工程规范；
5. 清晰的开发环境、可靠测试和明确文档会显著提高 Codex 执行工程任务的稳定性；
6. Skills 更适合作为可组合的小型工作流积木，而不是一个巨大的端到端黑箱。

---

## 十二、最终原则

> **Codex 不负责“凭灵感造 3D”。**
>
> **Codex 负责让资产编译器持续变得更聪明、更完整、更可靠。**

最终理想状态是：

```text
用户说：
“把这个门派场景编译成我们世界观里的游戏资产。”

Codex 不重新发明建模方法。
它识别并组合已有 Skills：

分析参考
→ 解析 Spec
→ 编译 Blender
→ Visual QA
→ 参数修复
→ 发现 Template Gap
→ 必要时升级 Factory
→ 验证 GLB
→ 引擎验收
```

这才是 Codex 在 Wuxia Asset Compiler 中最有价值的位置。
