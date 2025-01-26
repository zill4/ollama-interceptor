# Ollama Interceptor 🔍

A sophisticated network interceptor designed to capture, log, and analyze traffic between IntelliJ and Ollama. This tool enables transparent monitoring of API communications while maintaining full functionality of both services.

## 🎯 Purpose

The Ollama Interceptor serves as a transparent proxy that:
- Captures all HTTP/HTTPS traffic between IntelliJ and Ollama
- Provides human-readable logs of requests and responses
- Maintains real-time communication without affecting performance
- Enables API analysis for development and debugging

## 🛠️ Components

### 1. Interceptor (ollama_interceptor.py)
- Transparent TCP proxy with HTTP parsing
- Real-time traffic logging
- Automatic protocol detection
- Bidirectional communication handling
- Structured logging with timestamps

### 2. Cleanup Script (ollama_cleanup.ps1)
- System configuration restoration
- Network stack cleanup
- Process management
- Firewall rule restoration
- Health checks and verification

## 📋 Requirements

- Python 3.7+
- Windows PowerShell (for cleanup script)
- Administrator privileges (for network configuration)

## 🚀 Quick Start

1. **Start the Interceptor**
```bash
python ollama_interceptor.py
```

2. **Monitor Traffic**
- Logs are written to `ollama_traffic.log`
- Real-time console output shows active connections
- Structured HTTP request/response logging

3. **Cleanup When Done**
```powershell
.\ollama_cleanup.ps1
```

## 📝 Log Format

```plaintext
CLIENT -> SERVER [2024-02-20 14:30:45.123456]
POST /api/generate HTTP/1.1
Headers:
  host: localhost:11434
  content-type: application/json
  content-length: 45
  user-agent: IntelliJ HTTP Client

Body:
{"model":"llama2","prompt":"Hello world"}
------------------------------------------------------------
```

## 🔒 Security Considerations

- Runs locally (localhost only)
- No modification of transmitted data
- Clean system restoration via cleanup script
- Temporary port forwarding (11434 → 11435)

## 🛡️ System Impact

The interceptor:
- Creates temporary port forwarding
- Adds firewall rules
- Maintains connection state
- Logs to local filesystem

All changes are reversible via the cleanup script.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⚠️ Disclaimer

This tool is designed for development and debugging purposes only. Use in accordance with your organization's security policies.

## 📄 License

MIT License - See LICENSE file for details

## 🔧 Troubleshooting

If you encounter connection issues:
1. Run the cleanup script
2. Verify Ollama is running
3. Check port availability
4. Review firewall settings

For persistent issues, check the logs for detailed error messages.

---
Created and maintained by [zill4](https://github.com/zill4)