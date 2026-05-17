
import React, { useState, useEffect } from "react";
import axios, { AxiosError } from "axios";
import { Typography, Table, Button, Select } from "antd";
import type { TableProps } from "antd";

const { Text } = Typography;
const { Option } = Select;

interface Inspection {
  id: number;
  filename: string;
  image_path: string;
  defects: Record<string, number>;
  timestamp: string;
}

const columns = [
  { title: "ID", dataIndex: "id", key: "id" },
  { title: "Имя файла", dataIndex: "filename", key: "filename" },
  { title: "Путь до файла", dataIndex: "image_path", key: "image_path" },
  {
    title: "Дефекты",
    dataIndex: "defects",
    key: "defects",
    render: (defects: Record<string, number>) => <span>{JSON.stringify(defects)}</span>,
  },
  {
    title: "Время проверки",
    dataIndex: "timestamp",
    key: "timestamp",
    render: (timestamp: string) => {
      const date = new Date(timestamp);
      const adjustedDate = new Date(date.getTime() + 3 * 60 * 60 * 1000);
      return (
        <span>
          {adjustedDate.toLocaleString("ru-RU", {
            timeZone: "Europe/Moscow",
            timeZoneName: "short",
          })}
        </span>
      );
    },
  },
];

const Database: React.FC = () => {
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [filteredInspections, setFilteredInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [defectFilter, setDefectFilter] = useState<string | null>(null);
  const [defectOptions, setDefectOptions] = useState<string[]>([]);

  const getData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<Inspection[]>("http://localhost:8000/database");
      setInspections(response.data);
      setFilteredInspections(response.data);

      const allDefects = new Set<string>();
      response.data.forEach((item) =>
        Object.keys(item.defects).forEach((d) => allDefects.add(d))
      );
      setDefectOptions(Array.from(allDefects));
    } catch (err) {
      setError(err instanceof AxiosError ? err.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (defectFilter === null) {
      setFilteredInspections(inspections);
    } else {
      setFilteredInspections(
        inspections.filter((item) => item.defects[defectFilter] > 0)
      );
    }
  }, [defectFilter, inspections]);

  const onSelectChange = (keys: React.Key[]) => setSelectedRowKeys(keys);

  const handleDelete = async () => {
    setLoading(true);
    try {
      await axios.delete("http://localhost:8000/inspections", {
        data: { ids: selectedRowKeys },
      });
      const updated = inspections.filter((item) => !selectedRowKeys.includes(item.id));
      setInspections(updated);
      setFilteredInspections(
        updated.filter((item) => (defectFilter ? item.defects[defectFilter] > 0 : true))
      );
      setSelectedRowKeys([]);
    } catch (err) {
      setError(err instanceof AxiosError ? err.message : "Ошибка удаления");
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (value: string | null) => {
    setDefectFilter(value);
  };

  return (
    <div>
      <div style={{ padding: 16, gap: 20, display: "flex" }}>
        <Button onClick={getData} loading={loading}>
          Получить данные из базы данных
        </Button>

        <Select
          data-testid="defect-select"
          placeholder="Выберите дефект для фильтрации"
          style={{ width: 200 }}
          allowClear
          onChange={handleFilterChange}
          value={defectFilter}
        >
          {defectOptions.map((d) => (
            <Option key={d} value={d}>
              {d}
            </Option>
          ))}
        </Select>

        <Button disabled={!selectedRowKeys.length} onClick={handleDelete} loading={loading}>
          Удалить выбранные
        </Button>

        {error && <Text type="danger">{error}</Text>}
      </div>

      {inspections.length > 0 ? (
        <Table
          data-testid="inspection-table"
          dataSource={filteredInspections}
          columns={columns}
          rowKey="id"
          rowSelection={{
            selectedRowKeys,
            onChange: onSelectChange,
          }}
        />
      ) : (
        <Text>Данные отсутствуют</Text>
      )}
    </div>
  );
};

export default Database;
