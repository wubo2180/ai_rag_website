# V3 Examples

本目录包含V3框架的示例和测试代码。

## 文件说明

### `test_layered_deskewing.py`
分层倾斜校正功能的完整测试示例。

**功能**:
- 测试3种分层校正方法（分步、加权、最佳）
- 对比传统方法与分层方法
- 生成详细的测试报告和可视化结果

**使用**:
```bash
cd V3/examples
python test_layered_deskewing.py
```

**输出**:
- `layered_deskewing_test/` - 分层方法测试结果
- `traditional_vs_layered_test/` - 传统vs分层对比
- JSON格式的详细测试报告

## 如何运行示例

1. 确保已安装依赖包
2. 准备输入PDF文件
3. 修改代码中的文件路径
4. 运行相应的示例脚本

## 注意事项

- 示例代码仅供参考和测试
- 生产环境请使用V3框架的正式API
- 测试会生成大量临时文件，运行后可自行清理

