import React from "react";
import ProcessedImage from "./ProcImg";
import Database from "./database";
import {Layout, Tabs, Typography} from 'antd';

const { Title, Text } = Typography;
const { Header, Content, Footer } = Layout;



const App: React.FC = () => {
  return (
    <Layout>
      
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <Text style={{ color: "white", margin: 0, fontSize:"45px" }}>Система распознавания дефектов печатных плат</Text>
      </Header>


      <Content style={{ padding: '0 48px' }}>
      <Tabs defaultActiveKey="1">

          <Tabs.TabPane tab="Распознавание" key="1">
            <Title level={2}>Распознавание дефектов</Title>
            <ProcessedImage/>
          </Tabs.TabPane>

          <Tabs.TabPane tab="База данных" key="2">
            <Title level={2}>База данных</Title>
            <Database/>
          </Tabs.TabPane>

        </Tabs>
      </Content>


      <Footer style={{ textAlign: 'center' }}>
      </Footer>
    </Layout>
  );
};

export default App;


