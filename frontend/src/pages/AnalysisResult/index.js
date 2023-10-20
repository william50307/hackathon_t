import React, { useState } from "react";
import { Modal, Upload, Button, Spin, message, Card } from "antd";
import { Row, Col } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import Layouts from "../../components/Layouts";
import TypingEffect from "../../utils/typingEffect";
import api from "../../utils/api";
import mock from "../../utils/mock";

const getBase64 = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
  });

function AnalysisResult() {
  const [fileList, setFileList] = useState([]);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewImage, setPreviewImage] = useState("");
  const [loading, setLoading] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [responseText, setResponseText] = useState("");
  const [isTypingComplete, setIsTypingComplete] = useState(false);
  const [result, setResult] = useState("");
  const [resultImage, setResultImage] = useState("");

  const handleTypingComplete = () => {
    setIsTypingComplete(true);
  };

  const handleUpload = () => {
    const backendServiceUrl = process.env.REACT_APP_BACKEND_SERVICE_URL;
    setLoading(true);

    if (fileList.length === 0) {
      message.warning("Please select an image to upload.");
      return;
    }

    const formData = new FormData();
    formData.append("image", fileList[0].originFileObj);

    // api.post(`${backendServiceUrl}/upload`, formData).then((res) => {(
    //   (response) => {
    //     if (response.status === 200) {
    //       setLoading(false);
    //       setShowResult(true);
    //       message.success("Image uploaded successfully.");
    //     } else {
    //       message.error("Failed to upload image.");
    //     }
    //     return response.text();
    //   })
    //   .then((text) => {
    //     console.log(text);
    //     setResponseText(text);
    //   })
    //   .catch((error) => {
    //     message.error("An error occurred while uploading the image.");
    //     console.log(error);
    //   });
    // });
    mock.fetchScanResult().then(async (res) => {
      const file = fileList[0];
      if (!file.url && !file.preview) {
        file.preview = await getBase64(file.originFileObj);
      }
      setResultImage(file.url || file.preview);
      setResult(res);
      setLoading(false);
      setShowResult(true);
      message.success("Image uploaded successfully.");
    });
  };

  const handleCancel = () => {
    setPreviewOpen(false);
  };

  const handleReset = () => {
    setPreviewImage("");
    // setPreviewOpen(false);
    // setResponseText("");
    setResultImage("");
    setResult("");
    setShowResult(false);
    setFileList([]);
  };

  const handleRemove = () => {
    setResponseText("");
  };

  const handlePreview = async (file) => {
    if (!file.url && !file.preview) {
      file.preview = await getBase64(file.originFileObj);
    }
    setPreviewImage(file.url || file.preview);
    setPreviewOpen(true);
  };

  const handleChange = (info) => {
    setFileList(info.fileList);
  };

  const uploadButton = (
    <div>
      <UploadOutlined />
      <div className="ant-upload-text">Upload</div>
    </div>
  );

  return (
    <Layouts>
      <Card>
        <div>
          <h1>Image Upload and Display</h1>
          <Row>
            <Col span={24}>
              {showResult ? (
                <div>
                  <TypingEffect
                    text={responseText}
                    speed={100}
                    onTypingComplete={handleTypingComplete}
                  />
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <img style={{ width: "100%" }} src={resultImage} />
                    </Col>
                    <Col span={12}>
                      <p>員工編號：{result.EmpId}</p>
                      <p>廠區：{result.Zone}</p>
                      <p>部門：{result.DeptId}</p>
                      <p>入廠時間：{result.DateTime}</p>
                      <p>圖片：{result.Img}</p>
                    </Col>
                  </Row>
                  <Button onClick={handleReset}>重新上傳</Button>
                </div>
              ) : (
                <div className="space-align-block">
                  <Upload
                    listType="picture-card"
                    fileList={fileList}
                    onChange={handleChange}
                    onPreview={handlePreview}
                    onRemove={handleRemove}
                    customRequest={({ onSuccess, onError, file }) => {
                      // Handle file upload logic here
                      // You can send the file to your server or process it as needed
                      // Example: send the file to a server using fetch
                      onSuccess();
                    }}
                  >
                    {fileList.length < 1 && uploadButton}
                  </Upload>
                  <Modal
                    open={previewOpen}
                    footer={null}
                    onCancel={handleCancel}
                  >
                    <img style={{ width: "100%" }} src={previewImage} />
                  </Modal>

                  <Button
                    type="primary"
                    onClick={handleUpload}
                    loading={loading}
                    disabled={fileList.length < 1}
                  >
                    分析
                  </Button>
                </div>
              )}
            </Col>
          </Row>

          <Spin spinning={loading}>{!loading}</Spin>
        </div>
      </Card>
    </Layouts>
  );
}
export default AnalysisResult;