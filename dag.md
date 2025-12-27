# Multi-Agent Debate DAG Diagram

```mermaid
flowchart TD
    START([START]) --> UI[UserInputNode<br/>Topic Validation]
    UI --> AGENT[AgentNode<br/>Scientist/Philosopher]
    AGENT --> MEM[MemoryNode<br/>Transcript & Summary]
    MEM --> LOG[LoggerNode<br/>Event Logging]
    LOG --> CTRL[RoundsControllerNode<br/>Turn Enforcement]
    CTRL --> |Round < 8| AGENT
    CTRL --> |Round = 8| JUDGE[JudgeNode<br/>Verdict & Summary]
    JUDGE --> FLOG[LoggerNode<br/>Final Log Write]
    FLOG --> END([END])
    
    subgraph debate_loop[Debate Loop - 8 Rounds]
        AGENT
        MEM
        LOG
        CTRL
    end
```