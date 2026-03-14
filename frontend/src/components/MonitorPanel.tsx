import React, { useState, useEffect } from 'react'
import { Modal, Tabs, Card, Tag, Spin, Alert, Typography, Space } from 'antd'
import { FileTextOutlined, MessageOutlined, RobotOutlined } from '@ant-design/icons'

const { Title, Text } = Typography
const { TabPane } = Tabs

interface MonitorData {
  id: string
  session_id: string
  round_number: number
  input: {
    user_message: string
    resume_data: any
    job_info: any
    history: any[]
  }
  prompt: {
    system_prompt: string
    full_messages: Array<{ role: string; content: string }>
    model: string
    temperature: number
  }
  output: {
    raw_response: string
    thinking_process: Array<{
      step: string
      status: string
      detail: string
    }>
    parsed_response: string
  }
  stats: {
    start_time: number
    end_time: number
    duration_ms: number
    step_durations: Record<string, number>
  }
  created_at: string
}

interface MonitorPanelProps {
  visible: boolean
  sessionId: string
  roundNumber?: number
  onClose: () => void
}

// JSON 格式化显示组件
const JSONView: React.FC<{ data: any }> = ({ data }) => {
  const formatValue = (value: any, indent: number = 0): React.ReactNode => {
    const spaces = '  '.repeat(indent)
    
    if (value === null) return <span style={{ color: '#999' }}>null</span>
    if (typeof value === 'string') return <span style={{ color: '#52c41a' }}>"{value}"</span>
    if (typeof value === 'number') return <span style={{ color: '#1890ff' }}>{value}</span>
    if (typeof value === 'boolean') return <span style={{ color: '#722ed1' }}>{value.toString()}</span>
    
    if (Array.isArray(value)) {
      if (value.length === 0) return <span>[]</span>
      return (
        <div>
          <div>[</div>
          {value.map((item, index) => (
            <div key={index} style={{ marginLeft: 16 }}>
              {formatValue(item, indent + 1)}
              {index < value.length - 1 && ','}
            </div>
          ))}
          <div>]</div>
        </div>
      )
    }
    
    if (typeof value === 'object') {
      const keys = Object.keys(value)
      if (keys.length === 0) return <span>{}</span>
      return (
        <div>
          <div>{'{'}</div>
          {keys.map((key, index) => (
            <div key={key} style={{ marginLeft: 16 }}>
              <span style={{ color: '#fa8c16' }}>"{key}"</span>: {formatValue(value[key], indent + 1)}
              {index < keys.length - 1 && ','}
            </div>
          ))}
          <div>{'}'}</div>
        </div>
      )
    }
    
    return <span>{String(value)}</span>
  }
  
  return (
    <div style={{ 
      background: '#1e1e1e', 
      color: '#d4d4d4',
      padding: 16, 
      borderRadius: 8,
      fontFamily: 'Consolas, Monaco, "Courier New", monospace',
      fontSize: 13,
      maxHeight: '60vh',
      overflow: 'auto',
      lineHeight: 1.6
    }}>
      {formatValue(data)}
    </div>
  )
}

// Token 计算
const estimateTokens = (text: string): number => {
  const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length
  const englishWords = (text.match(/[a-zA-Z]+/g) || []).length
  const otherChars = text.length - chineseChars - englishWords
  return Math.ceil(chineseChars * 1.5 + englishWords * 1.3 + otherChars * 0.5)
}

const MonitorPanel: React.FC<MonitorPanelProps> = ({
  visible,
  sessionId,
  roundNumber,
  onClose
}) => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [monitorData, setMonitorData] = useState<MonitorData | MonitorData[] | null>(null)
  const [selectedRound, setSelectedRound] = useState<number>(roundNumber || 1)

  useEffect(() => {
    if (visible && sessionId) {
      fetchMonitorData()
    }
  }, [visible, sessionId, roundNumber])

  const fetchMonitorData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const url = roundNumber 
        ? `/api/v1/chat/monitor/${sessionId}?round_number=${roundNumber}`
        : `/api/v1/chat/monitor/${sessionId}`
      
      const response = await fetch(url)
      
      if (!response.ok) {
        if (response.status === 404) {
          setError('监控数据不存在')
          return
        }
        throw new Error('获取监控数据失败')
      }
      
      const data = await response.json()
      setMonitorData(data)
      
      if (Array.isArray(data) && data.length > 0) {
        setSelectedRound(data[0].round_number)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知错误')
    } finally {
      setLoading(false)
    }
  }

  const getCurrentRoundData = (): MonitorData | null => {
    if (!monitorData) return null
    if (Array.isArray(monitorData)) {
      return monitorData.find(d => d.round_number === selectedRound) || monitorData[0] || null
    }
    return monitorData
  }

  const data = getCurrentRoundData()

  // 第一个 Tab：简历完整数据
  const renderResumeTab = () => {
    if (!data) return null
    
    return (
      <div>
        <div style={{ marginBottom: 16 }}>
          <Text type="secondary">简历完整数据（原始输入）</Text>
        </div>
        <JSONView data={data.input.resume_data} />
      </div>
    )
  }

  // 第二个 Tab：完整提示词
  const renderPromptTab = () => {
    if (!data) return null
    
    // 构建完整提示词
    const fullPrompt = data.prompt.full_messages.map(msg => {
      const roleLabel = msg.role === 'system' ? '【系统】' : msg.role === 'user' ? '【用户】' : '【AI】'
      return `${roleLabel}\n${msg.content}`
    }).join('\n\n---\n\n')
    
    const totalTokens = estimateTokens(fullPrompt)
    
    return (
      <div>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text type="secondary">实际输入给 LLM 的完整提示词</Text>
          <Space>
            <Tag color="blue">模型: {data.prompt.model}</Tag>
            <Tag color="green">温度: {data.prompt.temperature}</Tag>
            <Tag color={totalTokens > 4000 ? 'red' : totalTokens > 2000 ? 'orange' : 'green'}>
              总 Token: ~{totalTokens}
            </Tag>
          </Space>
        </div>
        <div style={{ 
          background: '#1e1e1e', 
          color: '#d4d4d4',
          padding: 16, 
          borderRadius: 8,
          fontFamily: 'Consolas, Monaco, "Courier New", monospace',
          fontSize: 13,
          maxHeight: '60vh',
          overflow: 'auto',
          lineHeight: 1.6,
          whiteSpace: 'pre-wrap'
        }}>
          {fullPrompt}
        </div>
      </div>
    )
  }

  // 第三个 Tab：LLM 实际输出
  const renderOutputTab = () => {
    if (!data) return null
    
    const fullResponse = data.output.full_response || data.output.raw_response || ''
    const summary = data.output.summary || ''
    
    // 计算 token 消耗
    const responseTokens = estimateTokens(fullResponse)
    const summaryTokens = estimateTokens(summary)
    const totalOutputTokens = responseTokens + summaryTokens
    
    return (
      <div>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text type="secondary">LLM 实际输出结果</Text>
          <Space>
            <Tag color="blue">回答: ~{responseTokens} tokens</Tag>
            <Tag color="purple">摘要: ~{summaryTokens} tokens</Tag>
            <Tag color={totalOutputTokens > 1000 ? 'red' : totalOutputTokens > 500 ? 'orange' : 'green'}>
              总输出: ~{totalOutputTokens} tokens
            </Tag>
          </Space>
        </div>
        
        {/* 完整回答 */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ 
            background: '#f6ffed', 
            padding: 16, 
            borderRadius: 8,
            border: '1px solid #b7eb8f',
            maxHeight: '40vh',
            overflow: 'auto',
            lineHeight: 1.8,
            fontSize: 14,
            whiteSpace: 'pre-wrap'
          }}>
            <div style={{ 
              marginBottom: 8, 
              fontWeight: 'bold', 
              color: '#52c41a',
              borderBottom: '1px solid #b7eb8f',
              paddingBottom: 8
            }}>
              📝 完整回答
            </div>
            {fullResponse}
          </div>
        </div>
        
        {/* 对话摘要 */}
        {summary && (
          <div style={{ 
            background: '#fff7e6', 
            padding: 16, 
            borderRadius: 8,
            border: '1px solid #ffd591',
            maxHeight: '20vh',
            overflow: 'auto',
            lineHeight: 1.8,
            fontSize: 14,
            whiteSpace: 'pre-wrap'
          }}>
            <div style={{ 
              marginBottom: 8, 
              fontWeight: 'bold', 
              color: '#fa8c16',
              borderBottom: '1px solid #ffd591',
              paddingBottom: 8
            }}>
              📋 对话摘要（用于后续上下文）
            </div>
            {summary}
          </div>
        )}
      </div>
    )
  }

  return (
    <Modal
      title={
        <Space>
          <span>对话监控面板</span>
          {Array.isArray(monitorData) && monitorData.length > 0 && (
            <Space size="small" style={{ marginLeft: 16 }}>
              {monitorData.map(d => (
                <Tag 
                  key={d.round_number}
                  color={selectedRound === d.round_number ? 'blue' : 'default'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSelectedRound(d.round_number)}
                >
                  第{d.round_number}轮
                </Tag>
              ))}
            </Space>
          )}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={1000}
      footer={null}
      styles={{ body: { maxHeight: '70vh', overflow: 'auto' } }}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>加载监控数据...</div>
        </div>
      ) : error ? (
        <Alert message={error} type="error" showIcon />
      ) : data ? (
        <Tabs defaultActiveKey="resume" type="card">
          <TabPane 
            tab={<span><FileTextOutlined /> 简历数据</span>} 
            key="resume"
          >
            {renderResumeTab()}
          </TabPane>
          <TabPane 
            tab={<span><MessageOutlined /> 完整提示词</span>} 
            key="prompt"
          >
            {renderPromptTab()}
          </TabPane>
          <TabPane 
            tab={<span><RobotOutlined /> LLM输出</span>} 
            key="output"
          >
            {renderOutputTab()}
          </TabPane>
        </Tabs>
      ) : (
        <Alert message="暂无监控数据" type="info" showIcon />
      )}
    </Modal>
  )
}

export default MonitorPanel
