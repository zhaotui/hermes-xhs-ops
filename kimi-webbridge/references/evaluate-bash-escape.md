# Evaluate Bash 传参方案

`evaluate` 的 `code` 字段通过 JSON 传递，然后作为 shell 命令的参数。当代码包含中文、单引号、换行、`$` 等特殊字符时，直接写在 curl 的 `-d` 参数里容易炸。

## 固定模式

**不要**直接在 bash 里写 JS 代码字符串。用三步法：

```bash
# 1. 写入 JS 到文件
cat > /tmp/eval.js << 'JS_EOF'
(() => {
  return JSON.stringify({ key: "值" });
})()
JS_EOF

# 2. 通过 python3 构造 JSON（避免 shell 转义问题）
CODE=$(cat /tmp/eval.js)
curl -s -X POST "http://172.26.240.1:10086/command" \
  -H 'Content-Type: application/json' \
  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'xhs'}))" "$CODE")"
```

## 为什么这样做

- `write_file` → 代码不进 shell 参数，避免引号炸
- `python3 -c` + `sys.argv[1]` → Python 处理 JSON 序列化，不会触发 bash 对中文逗号 `，`、单引号等字符的误解析
- 如果代码中包含 `$`，`python3` 方案天然不受 bash 变量展开影响
