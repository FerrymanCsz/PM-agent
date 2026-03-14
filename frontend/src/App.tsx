import React, { useState, useEffect } from 'react'
import { Layout, Menu, Button, Modal, message, Empty, Dropdown } from 'antd'
import { 
  MessageOutlined, 
  BookOutlined, 
  FileTextOutlined, 
  SettingOutlined, 
  ApiOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  MoreOutlined
} from '@ant-design/icons'
import ChatPage from './pages/ChatPage'
import ResumePage from './pages/ResumePage'
import JobPage from './pages/JobPage'
import LLMConfigPage from './pages/LLMConfigPage'
import KnowledgePage from './pages/KnowledgePage'
import './App.css'

const { Header, Sider, Content } = Layout

type PageType = 'chat' | 'resume' | 'knowledge' | 'job' | 'llm-config'

interface Session {
  id: string
  title: string
  status: string
  message_count: number
  created_at: string
  updated_at: string
}

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageType>('chat')
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string>('')
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [editingSession, setEditingSession] = useState<Session | null>(null)
  const [newTitle, setNewTitle] = useState('')

  // 获取会话列表
  const fetchSessions = async () => {
    setLoadingSessions(true)
    try {
      const response = await fetch('/api/v1/chat/sessions')
      if (response.ok) {
        const data = await response.json()
        setSessions(data)
      }
    } catch (error) {
      console.error('获取会话列表失败:', error)
    } finally {
      setLoadingSessions(false)
    }
  }

  useEffect(() => {
    fetchSessions()
  }, [currentSessionId])

  // 创建新面试
  const handleNewInterview = () => {
    setCurrentSessionId('')
    setCurrentPage('chat')
    message.success('已创建新面试，开始提问吧！')
  }

  // 切换到指定会话
  const handleSwitchSession = (sessionId: string) => {
    setCurrentSessionId(sessionId)
    setCurrentPage('chat')
  }

  // 删除会话
  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个面试记录吗？删除后无法恢复。',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await fetch(`/api/v1/chat/sessions/${sessionId}`, {
            method: 'DELETE'
          })
          if (response.ok) {
            message.success('删除成功')
            if (currentSessionId === sessionId) {
              setCurrentSessionId('')
            }
            fetchSessions()
          } else {
            message.error('删除失败')
          }
        } catch (error) {
          message.error('删除失败')
        }
      }
    })
  }

  // 重命名会话
  const handleRenameSession = (session: Session, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingSession(session)
    setNewTitle(session.title)
  }

  // 保存新标题
  const handleSaveTitle = async () => {
    if (!editingSession || !newTitle.trim()) return
    
    try {
      const response = await fetch(`/api/v1/chat/sessions/${editingSession.id}/title`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle.trim() })
      })
      
      if (response.ok) {
        message.success('重命名成功')
        fetchSessions()
      } else {
        message.error('重命名失败')
      }
    } catch (error) {
      message.error('重命名失败')
    } finally {
      setEditingSession(null)
      setNewTitle('')
    }
  }

  const renderContent = () => {
    switch (currentPage) {
      case 'chat':
        return <ChatPage 
          key={currentSessionId || 'new'} 
          sessionId={currentSessionId} 
          onSessionCreated={(id) => {
            setCurrentSessionId(id)
            fetchSessions()
          }}
        />
      case 'resume':
        return <ResumePage />
      case 'knowledge':
        return <KnowledgePage />
      case 'job':
        return <JobPage />
      case 'llm-config':
        return <LLMConfigPage />
      default:
        return <ChatPage key="new" sessionId="" onSessionCreated={() => {}} />
    }
  }

  // 顶部菜单项
  const headerMenuItems = [
    {
      key: 'resume',
      icon: <FileTextOutlined />,
      label: '简历',
      onClick: () => setCurrentPage('resume')
    },
    {
      key: 'knowledge',
      icon: <BookOutlined />,
      label: '知识库',
      onClick: () => setCurrentPage('knowledge')
    },
    {
      key: 'job',
      icon: <SettingOutlined />,
      label: '岗位',
      onClick: () => setCurrentPage('job')
    }
  ]

  // 按日期分组会话
  const groupSessionsByDate = (sessions: Session[]) => {
    const groups: { [key: string]: Session[] } = {}
    
    sessions.forEach(session => {
      const date = new Date(session.updated_at)
      const today = new Date()
      const yesterday = new Date(today)
      yesterday.setDate(yesterday.getDate() - 1)
      
      let key: string
      if (date.toDateString() === today.toDateString()) {
        key = '今天'
      } else if (date.toDateString() === yesterday.toDateString()) {
        key = '昨天'
      } else {
        key = date.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })
      }
      
      if (!groups[key]) {
        groups[key] = []
      }
      groups[key].push(session)
    })
    
    return groups
  }

  const sessionGroups = groupSessionsByDate(sessions)
  const sortedKeys = Object.keys(sessionGroups).sort((a, b) => {
    if (a === '今天') return -1
    if (b === '今天') return 1
    if (a === '昨天') return -1
    if (b === '昨天') return 1
    return 0
  })

  // 构建侧边栏菜单项（仅会话列表）
  const buildSiderItems = () => {
    const items: any[] = []

    // 添加会话分组
    sortedKeys.forEach((dateKey, groupIndex) => {
      items.push({
        type: 'group',
        key: `group-${groupIndex}`,
        label: dateKey,
        children: sessionGroups[dateKey].map(session => ({
          key: session.id,
          label: (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              width: '100%'
            }}>
              <span style={{ 
                overflow: 'hidden', 
                textOverflow: 'ellipsis', 
                whiteSpace: 'nowrap',
                flex: 1
              }}>
                {session.title}
              </span>
              <Dropdown
                menu={{
                  items: [
                    {
                      key: 'rename',
                      icon: <EditOutlined />,
                      label: '重命名',
                      onClick: (e: any) => handleRenameSession(session, e.domEvent)
                    },
                    {
                      key: 'delete',
                      icon: <DeleteOutlined />,
                      label: '删除',
                      danger: true,
                      onClick: (e: any) => handleDeleteSession(session.id, e.domEvent)
                    }
                  ]
                }}
                trigger={['click']}
              >
                <Button
                  type="text"
                  size="small"
                  icon={<MoreOutlined />}
                  onClick={(e) => e.stopPropagation()}
                  style={{ marginLeft: '8px' }}
                />
              </Dropdown>
            </div>
          ),
          onClick: () => handleSwitchSession(session.id)
        }))
      })
    })

    // 如果没有会话，显示提示
    if (sessions.length === 0) {
      items.push({
        key: 'empty',
        disabled: true,
        label: (
          <Empty 
            image={Empty.PRESENTED_IMAGE_SIMPLE} 
            description="暂无面试记录"
            style={{ padding: '20px 0' }}
          />
        )
      })
    }

    return items
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', borderBottom: '1px solid #f0f0f0' }}>
        <div style={{ fontSize: '18px', fontWeight: 'bold', marginRight: 'auto' }}>
          面试模拟Agent系统
        </div>
        <Menu 
          mode="horizontal" 
          style={{ border: 'none' }} 
          selectedKeys={[currentPage]}
          items={headerMenuItems}
        />
      </Header>
      <Layout>
        <Sider width={280} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
          <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
            {/* 新面试按钮 - 固定顶部 */}
            <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0', flexShrink: 0 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleNewInterview}
                style={{ 
                  width: '100%',
                  background: currentPage === 'chat' && !currentSessionId ? '#1890ff' : '#52c41a'
                }}
                size="large"
              >
                新面试
              </Button>
            </div>
            
            {/* 会话列表 - 可滚动区域 */}
            <div style={{ flex: 1, overflow: 'auto' }}>
              <Menu 
                mode="inline" 
                selectedKeys={[currentSessionId || (currentPage === 'chat' ? 'new-chat' : currentPage)]}
                style={{ borderRight: 0 }}
                items={buildSiderItems()}
              />
            </div>
            
            {/* 底部导航 - 固定底部 */}
            <div style={{ borderTop: '1px solid #f0f0f0', flexShrink: 0 }}>
              <Menu 
                mode="inline" 
                selectedKeys={[currentPage]}
                style={{ borderRight: 0 }}
                items={[
                  {
                    key: 'knowledge',
                    icon: <BookOutlined />,
                    label: '知识库',
                    onClick: () => setCurrentPage('knowledge')
                  },
                  {
                    key: 'resume',
                    icon: <FileTextOutlined />,
                    label: '简历管理',
                    onClick: () => setCurrentPage('resume')
                  },
                  {
                    key: 'job',
                    icon: <SettingOutlined />,
                    label: '岗位设置',
                    onClick: () => setCurrentPage('job')
                  },
                  {
                    key: 'llm-config',
                    icon: <ApiOutlined />,
                    label: 'LLM配置',
                    onClick: () => setCurrentPage('llm-config')
                  }
                ]}
              />
            </div>
          </div>
        </Sider>
        <Content style={{ background: '#f5f5f5', padding: '24px' }}>
          {renderContent()}
        </Content>
      </Layout>

      {/* 重命名弹窗 */}
      <Modal
        title="重命名面试"
        open={!!editingSession}
        onOk={handleSaveTitle}
        onCancel={() => {
          setEditingSession(null)
          setNewTitle('')
        }}
        okText="保存"
        cancelText="取消"
      >
        <input
          type="text"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="输入新名称"
          style={{ 
            width: '100%', 
            padding: '8px 12px', 
            border: '1px solid #d9d9d9', 
            borderRadius: '4px',
            fontSize: '14px'
          }}
          autoFocus
        />
      </Modal>
    </Layout>
  )
}

export default App
