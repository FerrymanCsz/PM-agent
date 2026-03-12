import React, { useState } from 'react'
import { Layout, Menu } from 'antd'
import { MessageOutlined, BookOutlined, FileTextOutlined, SettingOutlined } from '@ant-design/icons'
import ChatPage from './pages/ChatPage'
import ResumePage from './pages/ResumePage'
import './App.css'

const { Header, Sider, Content } = Layout

type PageType = 'chat' | 'resume' | 'knowledge' | 'job'

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageType>('chat')

  const renderContent = () => {
    switch (currentPage) {
      case 'chat':
        return <ChatPage />
      case 'resume':
        return <ResumePage />
      case 'knowledge':
        return <div style={{ padding: '24px' }}>知识库管理（开发中）</div>
      case 'job':
        return <div style={{ padding: '24px' }}>岗位设置（开发中）</div>
      default:
        return <ChatPage />
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', borderBottom: '1px solid #f0f0f0' }}>
        <div style={{ fontSize: '18px', fontWeight: 'bold', marginRight: 'auto' }}>
          面试模拟Agent系统
        </div>
        <Menu mode="horizontal" style={{ border: 'none' }} selectedKeys={[currentPage]}>
          <Menu.Item key="resume" icon={<FileTextOutlined />} onClick={() => setCurrentPage('resume')}>
            简历
          </Menu.Item>
          <Menu.Item key="knowledge" icon={<BookOutlined />} onClick={() => setCurrentPage('knowledge')}>
            知识库
          </Menu.Item>
          <Menu.Item key="job" icon={<SettingOutlined />} onClick={() => setCurrentPage('job')}>
            岗位
          </Menu.Item>
        </Menu>
      </Header>
      <Layout>
        <Sider width={280} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
          <Menu 
            mode="inline" 
            selectedKeys={[currentPage]} 
            style={{ height: '100%', borderRight: 0 }}
          >
            <Menu.Item 
              key="chat" 
              icon={<MessageOutlined />} 
              onClick={() => setCurrentPage('chat')}
              style={{ margin: '16px', background: '#1890ff', color: '#fff', borderRadius: '4px' }}
            >
              + 新面试
            </Menu.Item>
            <Menu.Divider />
            <Menu.ItemGroup title="今天">
              <Menu.Item key="chat1" onClick={() => setCurrentPage('chat')}>模拟面试1</Menu.Item>
              <Menu.Item key="chat2" onClick={() => setCurrentPage('chat')}>模拟面试2</Menu.Item>
            </Menu.ItemGroup>
            <Menu.ItemGroup title="昨天">
              <Menu.Item key="chat3" onClick={() => setCurrentPage('chat')}>后端开发面试</Menu.Item>
            </Menu.ItemGroup>
            <Menu.Divider />
            <Menu.Item key="knowledge-base" icon={<BookOutlined />} onClick={() => setCurrentPage('knowledge')}>
              知识库
            </Menu.Item>
            <Menu.Item key="resume-manage" icon={<FileTextOutlined />} onClick={() => setCurrentPage('resume')}>
              简历管理
            </Menu.Item>
            <Menu.Item key="job-config" icon={<SettingOutlined />} onClick={() => setCurrentPage('job')}>
              岗位设置
            </Menu.Item>
          </Menu>
        </Sider>
        <Content style={{ background: '#f5f5f5', padding: '24px' }}>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  )
}

export default App
