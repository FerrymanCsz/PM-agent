import React, { useState, useRef, useEffect } from 'react'
import { Card, Input, Button, Space, Typography, Spin, Collapse, Tag, message } from 'antd'
import { SendOutlined, UserOutlined, RobotOutlined, LoadingOutlined, EyeOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import MonitorPanel from '../components/MonitorPanel'

const { TextArea } = Input
const { Title, Text } = Typography
const { Panel } = Collapse

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  thinking?: ThinkingStep[]
  summary?: string  // 对话摘要
  timestamp: Date
}

interface ThinkingStep {
  step: string
  status: string
  detail: string
}

interface ResumeData {
  id?: string
  name: string
  education: Array<{ school: string; major: string; degree?: string }>
  experience: Array<{ company: string; position: string; description?: string }>
  skills?: string[]
  projects?: Array<{ name: string; description?: string; role?: string }>
}

interface JobData {
  company: string
  position: string
  level?: string
}

interface ChatPageProps {
  sessionId?: string
  onSessionCreated?: (id: string) => void
}

const ChatPage: React.FC<ChatPageProps> = ({ sessionId: propSessionId, onSessionCreated }) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [thinkingProcess, setThinkingProcess] = useState<ThinkingStep[]>([])
  const [resumeData, setResumeData] = useState<ResumeData | null>(null)
  const [jobData, setJobData] = useState<JobData | null>(null)
  const [loadingConfig, setLoadingConfig] = useState(true)
  const [sessionId, setSessionId] = useState<string>(propSessionId || '')
  const [monitorVisible, setMonitorVisible] = useState(false)
  const [currentRound, setCurrentRound] = useState(1)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 获取当前简历和岗位配置，以及历史消息
  useEffect(() => {
    const fetchConfig = async () => {
      setLoadingConfig(true)
      try {
        // 获取当前简历
        const resumeResponse = await fetch('/api/v1/resumes/current')
        if (resumeResponse.ok) {
          const resume = await resumeResponse.json()
          // 将简历ID合并到parsed_data中
          setResumeData({
            id: resume.id,
            ...resume.parsed_data
          })
        }

        // 获取当前岗位配置
        const jobResponse = await fetch('/api/v1/jobs/current')
        if (jobResponse.ok) {
          const job = await jobResponse.json()
          setJobData(job)
        }

        // 如果有sessionId，加载历史消息
        if (propSessionId) {
          const historyResponse = await fetch(`/api/v1/chat/sessions/${propSessionId}/messages`)
          if (historyResponse.ok) {
            const data = await historyResponse.json()
            setSessionId(propSessionId)
            
            // 转换消息格式
            const historyMessages: Message[] = data.messages.map((m: any) => ({
              id: m.id,
              role: m.role,
              content: m.content,
              thinking: m.meta_data?.thinking_process,
              timestamp: new Date(m.created_at)
            }))
            setMessages(historyMessages)
            setCurrentRound(Math.ceil(historyMessages.length / 2) + 1)
          }
        } else {
          // 新会话，清空消息
          setMessages([])
          setSessionId('')
          setCurrentRound(1)
        }
      } catch (error) {
        console.error('获取配置失败:', error)
        message.warning('无法获取简历或岗位配置，将使用默认设置')
      } finally {
        setLoadingConfig(false)
      }
    }

    fetchConfig()
  }, [propSessionId])

  // 发送消息
  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setThinkingProcess([])

    try {
      // 调用后端API（非流式版本用于测试）
      const response = await fetch('/api/v1/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionId || undefined,
          message: userMessage.content,
          resume_data: resumeData || {
            name: '候选人',
            education: [],
            experience: []
          },
          job_info: jobData || {
            company: '未知公司',
            position: '未知岗位'
          },
          history: messages.map(m => ({
            role: m.role,
            content: m.content,
            summary: m.summary  // 传递对话摘要
          }))
        })
      })

      if (!response.ok) {
        throw new Error('请求失败')
      }

      const data = await response.json()
      
      // 保存 session_id
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id)
        // 通知父组件新会话已创建
        if (onSessionCreated) {
          onSessionCreated(data.session_id)
        }
      }
      
      // 更新当前轮次（请求成功后）
      setCurrentRound(prev => prev + 1)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        thinking: data.thinking_process,
        summary: data.summary,  // 保存对话摘要
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
      setThinkingProcess(data.thinking_process || [])
    } catch (error) {
      console.error('发送消息失败:', error)
      // 添加错误消息，显示具体错误
      const errorDetail = error instanceof Error ? error.message : '未知错误'
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `抱歉，服务暂时不可用。\n\n错误详情：${errorDetail}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  // 处理回车键
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{ height: 'calc(100vh - 112px)', display: 'flex', flexDirection: 'column' }}>
      {/* 聊天标题 */}
      <Card style={{ marginBottom: '16px' }}>
        <Space>
          <Title level={4} style={{ margin: 0 }}>面试模拟</Title>
          {loadingConfig ? (
            <Tag color="default">加载中...</Tag>
          ) : jobData ? (
            <Tag color="blue">{jobData.company} · {jobData.position}{jobData.level ? ` · ${jobData.level}` : ''}</Tag>
          ) : (
            <Tag color="orange">未配置岗位</Tag>
          )}
          {resumeData && (
            <Tag color="green">{resumeData.name}</Tag>
          )}
          {sessionId && (
            <Button 
              type="link" 
              icon={<EyeOutlined />}
              onClick={() => setMonitorVisible(true)}
            >
              监控面板
            </Button>
          )}
        </Space>
      </Card>

      {/* 消息列表 */}
      <Card style={{ flex: 1, overflow: 'auto', marginBottom: '16px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
              <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
              <p>开始面试吧！输入面试问题，Agent会以求职者身份回答。</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              style={{
                display: 'flex',
                justifyContent: message.role === 'user' ? 'flex-start' : 'flex-end',
                gap: '12px'
              }}
            >
              {message.role === 'user' && (
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#1890ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <UserOutlined style={{ color: '#fff', fontSize: '20px' }} />
                </div>
              )}

              <div style={{ maxWidth: '70%' }}>
                <div style={{ marginBottom: '4px', fontSize: '12px', color: '#999' }}>
                  {message.role === 'user' ? '面试官（我）' : 'Agent（面试者）'}
                  {' '}
                  {message.timestamp.toLocaleTimeString()}
                </div>

                <div
                  style={{
                    padding: '12px 16px',
                    borderRadius: '8px',
                    background: message.role === 'user' ? '#f0f0f0' : '#e6f7ff',
                    border: message.role === 'user' ? '1px solid #d9d9d9' : '1px solid #91d5ff'
                  }}
                >
                  {message.role === 'assistant' && message.thinking && message.thinking.length > 0 && (
                    <Collapse ghost style={{ marginBottom: '8px' }}>
                      <Panel
                        header={<Text type="secondary">思考过程 ({message.thinking.length} 步)</Text>}
                        key="thinking"
                      >
                        {message.thinking.map((step, index) => (
                          <div key={index} style={{ marginBottom: '8px', padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
                            <Text strong>{step.step}</Text>
                            <div style={{ fontSize: '12px', color: '#666' }}>{step.detail}</div>
                          </div>
                        ))}
                      </Panel>
                    </Collapse>
                  )}

                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>
              </div>

              {message.role === 'assistant' && (
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#52c41a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <RobotOutlined style={{ color: '#fff', fontSize: '20px' }} />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <div style={{ maxWidth: '70%' }}>
                <div style={{ marginBottom: '4px', fontSize: '12px', color: '#999' }}>
                  Agent（面试者）正在思考...
                </div>
                <div style={{ padding: '12px 16px', borderRadius: '8px', background: '#e6f7ff', border: '1px solid #91d5ff' }}>
                  <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
                  {thinkingProcess.length > 0 && (
                    <div style={{ marginTop: '8px' }}>
                      {thinkingProcess.map((step, index) => (
                        <div key={index} style={{ fontSize: '12px', color: '#666' }}>
                          {step.step}: {step.status === 'completed' ? '✓' : '⏳'} {step.detail}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#52c41a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <RobotOutlined style={{ color: '#fff', fontSize: '20px' }} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </Card>

      {/* 输入框 */}
      <Card>
        <Space style={{ width: '100%' }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入面试问题..."
            autoSize={{ minRows: 2, maxRows: 4 }}
            style={{ width: 'calc(100vw - 500px)' }}
            disabled={isLoading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={isLoading}
            disabled={!inputValue.trim()}
            size="large"
          >
            发送
          </Button>
        </Space>
      </Card>
      
      {/* 监控面板弹窗 */}
      <MonitorPanel
        visible={monitorVisible}
        sessionId={sessionId}
        roundNumber={currentRound - 1}
        onClose={() => setMonitorVisible(false)}
      />
    </div>
  )
}

export default ChatPage
