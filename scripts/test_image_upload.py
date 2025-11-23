"""
測試照片上傳功能的 base64 編碼
"""
import base64

def test_base64_encoding():
    """測試圖片 base64 編碼功能"""
    # 模擬圖片數據 (簡單的字節數據)
    fake_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    
    # 測試編碼
    encoded = base64.b64encode(fake_image_data).decode('utf-8')
    
    # 測試解碼
    decoded = base64.b64decode(encoded)
    
    print(f"原始數據: {fake_image_data}")
    print(f"Base64 編碼: {encoded}")
    print(f"解碼後數據: {decoded}")
    print(f"編碼解碼是否相同: {fake_image_data == decoded}")
    print("Base64 編碼測試完成！")
    
    return encoded

if __name__ == "__main__":
    test_result = test_base64_encoding()
    print(f"\n成功生成測試用的 base64 字串: {test_result[:50]}...")
