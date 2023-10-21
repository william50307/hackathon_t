import React, { useState, useEffect } from "react";
import dayjs from "dayjs";
import { useNavigate } from "react-router-dom";
import {
  Col,
  Card,
  Table,
  Button,
  Input,
  Form,
  Select,
  DatePicker,
} from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import mock from "../../../utils/mock";
import api from "../../../utils/api";

const { RangePicker } = DatePicker;

const weekFormat = "YYYY-MM-DD";

// Search Bar
const SearchForm = (props) => {
  const form = Form.useFormInstance();
  // TODO - fetch from data
  const zoneOptions = [
    {
      label: "ALL",
      value: "ALL",
    },
    {
      label: "HQ",
      value: "HQ",
    },
    {
      label: "AZ",
      value: "AZ",
    },
  ];

  const deptOptions = [
    {
      label: "DEPT1",
      value: "DEPT1",
    },
    {
      label: "DEPT2",
      value: "DEPT2",
    },
    {
      label: "DEPT3",
      value: "DEPT3",
    },
    {
      label: "DEPT4",
      value: "DEPT4",
    },
  ];

  const handleSearchClick = () => {
    const date = form.getFieldValue("date");
    const zone = form.getFieldValue("zone");
    const dept = form.getFieldValue("dept");
    props.search(date, zone, dept);
  };

  // 查詢 & 下載功能
  return (
    <div style={{ display: "contents" }}>
      <Form.Item
        name="date"
        label="日期範圍"
        initialValue={[
          dayjs("2023-09-11", weekFormat),
          dayjs("2023-09-17", weekFormat),
        ]}
      >
        <RangePicker placeholder={["開始時間", "結束時間"]} />
      </Form.Item>
      <Form.Item name="zone" label="廠區" initialValue={"ALL"}>
        <Select
          placeholder="Please select"
          style={{
            width: "100%",
          }}
          options={zoneOptions}
        />
      </Form.Item>

      <Form.Item name="dept" label="部門" initialValue={"DEPT1"}>
        <Select
          placeholder="Please select"
          style={{
            width: "100%",
          }}
          options={deptOptions}
        />
      </Form.Item>
      {/* <Form.Item name="empId">
        <Input placeholder="搜尋員工編號" />
      </Form.Item> */}
      <div style={{ display: "flex", marginLeft: "auto" }}>
        <Form.Item name="search">
          <Button type="primary" onClick={() => handleSearchClick()}>
            查詢
          </Button>
        </Form.Item>
        {/* <Button
          style={{ justifyContent: "flex-end" }}
          type="primary"
          icon={<DownloadOutlined />}
        /> */}
      </div>
    </div>
  );
};

// Table

const ItemMapping = {
  1: "電子設備",
  2: "筆記型電腦",
  3: "剪刀",
  4: "刀",
  5: "槍枝",
};

const columns = [
  {
    title: "入廠時間",
    dataIndex: "datetime",
  },
  {
    title: "廠區",
    dataIndex: "zone",
  },
  {
    title: "員工編號",
    dataIndex: "empid",
  },
  {
    title: "部門",
    dataIndex: "depid",
  },
  {
    title: "攜帶違禁品",
    dataIndex: "itemList",
    render: (items) => {
      const itemText = items.map((item) => ItemMapping[item]).join(", ");
      return itemText;
    },
  },
];

const EntryRecord = () => {
  const [contrabandHis, setContrabandHis] = useState();
  const [loading, setLoading] = useState(true);
  const [form] = Form.useForm();

  const search = (date, zone, dept) => {
    const rq = {
      start_time: dayjs(date[0]).format(weekFormat),
      end_time: dayjs(date[1]).format(weekFormat),
      depId: dept,
      zone: zone,
    };

    api
      .post("attend", rq)
      .then((res) => {
        const hisList = res["data"];
        for (const his of hisList) {
          const itemList = [];
          for (let i = 1; i <= 5; i++) {
            if (his["type" + i] === "1") {
              itemList.push(i);
            }
          }
          his["itemList"] = itemList;
          // console.log(his["itemList"]);
        }
        setContrabandHis(hisList);
        setLoading(false);
      })
      .catch((error) => {
        setContrabandHis([]);
        setLoading(false);
      });
  };

  useEffect(() => {
    const rq = {
      start_time: "2023-09-11",
      end_time: "2023-09-13",
      depId: "DEPT1",
      zone: "ALL",
    };

    api
      .post("attend", rq)
      .then((res) => {
        const hisList = res["data"];
        for (const his of hisList) {
          const itemList = [];
          for (let i = 1; i <= 5; i++) {
            if (his["type" + i] === "1") {
              itemList.push(i);
            }
          }
          his["itemList"] = itemList;
        }
        setContrabandHis(hisList);
        setLoading(false);
      })
      .catch((error) => {
        setContrabandHis([]);
        setLoading(false);
      });
  }, [form]);

  return (
    <Card>
      <Form form={form} layout="inline" style={{ padding: "0 0 16px 0" }}>
        <SearchForm search={search} />
      </Form>
      <Col span={24}>
        <Table
          dataSource={contrabandHis}
          columns={columns}
          loading={loading}
          rowKey={(record) => record.entryid}
        />
      </Col>
    </Card>
  );
};
export default EntryRecord;