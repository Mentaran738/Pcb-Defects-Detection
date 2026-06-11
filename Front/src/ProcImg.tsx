import React, { useEffect, useState } from "react";
import { Image, Typography, theme } from "antd";

const { Text, Title } = Typography;

const WEBSOCKET_URL = "ws://localhost:8000/ws";

const ProcessedImage: React.FC = () => {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [detections, setDet] = useState<string[]>([]);

  useEffect(() => {

    const socket = new WebSocket(WEBSOCKET_URL);

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.image) setImageUrl(data.image);
      if (data.defects) {
        setDet(Object.entries(data.defects).map(
          ([key, value]) => `${key}: ${value}`
        ));
      }
    };

    return () => socket.close();
  }, []);

  return (
    <div style={{ background: colorBgContainer, minHeight: 240, padding: 24, borderRadius: borderRadiusLG }}>
      <div style={{ margin: 10 }}>
        {imageUrl ? (
          <div style={{ display: "flex", alignItems: "flex-start", gap: "20px" }}>
            <Image src={imageUrl} width={"30%"} />
            <div>
              <Title level={3}>Найденные дефекты:</Title>
              {detections.length > 0 ? (
                detections.map((defect, index) => (
                  <Text key={index} type="danger" style={{ display: "block", fontSize: "30px" }}>
                    {defect}
                  </Text>
                ))
              ) : (
                <Text type="success" style={{ fontSize: "30px" }}>
                  Дефекты не обнаружены
                </Text>
              )}
            </div>
          </div>
        ) : (
          <p>Ожидание изображения...</p>
        )}
      </div>
    </div>
  );
};

export default ProcessedImage;
