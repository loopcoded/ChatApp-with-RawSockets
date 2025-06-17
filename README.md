# 🔐 ChatSecure – Encrypted Multi-Client Chat Application Over Raw TCP Sockets

**A low-level, real-time chat system** built from the ground up using **Python sockets** and **RSA encryption**, supporting **multi-client communication**, **private messaging**, **secure file transfers**, and a **Tkinter-based GUI** and now **user authentication with duplicate login prevention** — all without using external chat frameworks.



---

## 🧠 Why This Project Stands Out

This is not just another chat app. `ChatSecure` is a **system-level networking project** that demonstrates:

- 📡 **Low-level networking**: Uses raw **TCP socket programming** and **multi-threading**
- 🔐 **End-to-End Encryption**: Implements **RSA public-key encryption** for all message transfers
- 🔐 **Login/Register Authentication**: Username-password system before accessing chat
- 🚫 **Duplicate Login Prevention**: A user can only be logged in once at a time
- 🧵 **Concurrency & Multi-client**: Handles multiple clients via threaded server design
- 💬 **Private Messaging Support**: Chat one-on-one with other users using commands
- 🗂️ **File Transfer with Consent**: Send files **only with recipient approval**
- 🖥️ **Custom GUI Client**: Built from scratch using **Tkinter** for real-time UX
- 💻 **CLI fallback client**: Lightweight command-line client included

> This project reflects deep understanding of computer networks, socket I/O, encryption, and process concurrency

![WhatsApp Image 2025-06-07 at 13 28 37_f777654a](https://github.com/user-attachments/assets/74ae4dd7-b891-42a6-b54e-d95328b8968f)
>3 clients connected where 2 are students and 1 is manager with 1 server

![WhatsApp Image 2025-06-13 at 16 02 44_e285663d](https://github.com/user-attachments/assets/a1db20cb-76e6-4263-b0d2-70a55374aca2)
>before entering to chat we have authentication system

![WhatsApp Image 2025-06-07 at 13 31 43_fd7b3f67](https://github.com/user-attachments/assets/af500323-d738-4e67-b091-0be62fc4b0d1)
>sending private message

![WhatsApp Image 2025-06-07 at 13 29 49_b2bd96c9](https://github.com/user-attachments/assets/06053978-a672-4070-ad41-f0b91b15fb80)
>sharing private files

![image](https://github.com/user-attachments/assets/95a6fdc3-746d-486d-b8ff-279cc200bd2c)
>asking permission to download the file to the reciever or not

![WhatsApp Image 2025-06-07 at 13 30 14_2033da66](https://github.com/user-attachments/assets/6e204601-30bd-4e63-b5dd-aca8edf8d500)
>confirmation of recieving file

![WhatsApp Image 2025-06-07 at 13 32 44_1d41ac66](https://github.com/user-attachments/assets/7e0f3cb2-b094-483c-a661-8085de494e96)
>manager chat of receiving private and public messages


![WhatsApp Image 2025-06-07 at 13 33 18_9000e408](https://github.com/user-attachments/assets/63164801-8a43-4a6a-8084-1014d60a419f)
>showcasing of exit of other clients

![WhatsApp Image 2025-06-07 at 13 11 34_09e21d48](https://github.com/user-attachments/assets/e75db05d-eeca-4d72-8756-66940b9919a4)
>server running at backend decrypting the messages

---

## 🧰 Tech Stack

| Layer       | Technology |
|-------------|------------|
| Networking  | Python Sockets (TCP), Threading |
| Encryption  | RSA via `cryptography` |
| Interface   | Tkinter (GUI), CLI |
| Auth System   | Username-password with duplicate prevention |
| File Handling | Binary stream transfer with user confirmation |
| Deployment  | Python 3.x |

---

## ✨ Features Overview

| Feature                | Description |
|------------------------|-------------|
| 🔐 Encrypted Messaging | All messages are encrypted with **RSA public key** |
| 👥 Multi-Client Support | Server can handle multiple concurrent clients |
| 💬 Private Messaging   | Send `/msg username message` to whisper |
| 📁 File Sharing        | Send binary files using `/file username file` |
| 🖥️ GUI Client (Tkinter)| Graphical interface with chat, input, file buttons |
| 🧵 Threaded Server     | Each client runs in a separate thread |
| 🧪 CLI Client (Optional)| Use terminal version for headless operation |
| 👤 **Login/Register UI**         | Auth screen before entering the chat |
| 🚫 **Duplicate Login Detection** | Prevents the same user from logging in multiple times |
| ✅ **File Transfer Confirmation**| Users must accept before receiving any files |
| 📜 **Persistent Server Key**     | RSA keys are saved and reused for consistent encryption |


---



## 🚀 Project Structure
```bash
chat-app-socket-rsa/
├── backend/
│   ├── server.py             # Multi-threaded encrypted server with auth + file routing
│   ├── rsa_utils.py          # RSA key utilities (encrypt, decrypt, generate)
│   ├── auth_utils.py         # Authentication handling with user store
│   ├── server_private.pem    # RSA private key
│   └── server_public.pem     # RSA public key (sent to clients)
├── client/
│   ├── cli_client.py         # Terminal-based chat client
│   ├── gui_client.py         # GUI chat client (Tkinter)
│   ├── run_gui.py            # Launch GUI with login/register first
│   ├── downloads/            # Received files auto-saved here
├── .gitignore
├── requirements.txt
└── README.md
