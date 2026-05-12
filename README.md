# Cloud File Storage & Publishing System

A multi-client cloud file storage application implemented with **TCP sockets** in Python, featuring a graphical user interface and support for concurrent file operations.

> Course: **CS408 — Computer Networks**, Sabancı University (Fall 2024)
> Course Project

---

## ⚠️ Academic Integrity Notice

This project was submitted as coursework for CS408 (Computer Networks) at Sabancı University in Fall 2024. **If you are a current CS408 student, do NOT copy this code.** Doing so violates Sabancı University's academic integrity policy and will be detected by plagiarism detection tools. This repository is published as a portfolio reference only.

---

## Overview

The system implements a centralized file-sharing platform where multiple clients can connect to a server simultaneously to upload, download, list, and delete text files. Each file is owned by the client who uploaded it, and other clients can browse and download shared files. File ownership and naming conflicts are handled through a server-side mapping mechanism.

## Features

**Server**
- Multi-threaded TCP server handling concurrent client connections
- GUI-based configuration of listening port and storage directory
- Persistent file ownership tracking via JSON metadata
- Real-time activity logging with timestamps
- Graceful handling of client disconnections and naming conflicts
- Automatic notification to file owners when their files are downloaded

**Client**
- GUI for connecting to the server with IP, port, and username
- File browser integration for uploads and download destination selection
- On-demand listing of all available files with owner information
- Upload, download, and delete operations for owned files
- Real-time activity log
- Real-time notifications when own files are downloaded by others

## Architecture

```
┌─────────────┐         TCP          ┌─────────────┐
│   Client 1  │ ◄──────────────────► │             │
└─────────────┘                      │             │
                                     │   Server    │
┌─────────────┐         TCP          │  (threaded) │
│   Client 2  │ ◄──────────────────► │             │
└─────────────┘                      │             │
                                     │  Storage:   │
┌─────────────┐         TCP          │  files/     │
│   Client N  │ ◄──────────────────► │  + JSON     │
└─────────────┘                      └─────────────┘
```

**Communication Protocol:** Custom pipe-delimited command protocol over TCP (e.g., `UPLOAD|filename|filesize`, `DOWNLOAD|filename|owner`, `LIST`, `DELETE|filename`).

## Tech Stack

`Python 3` · `socket` · `threading` · `tkinter` · `json`

## Repository Contents

- `server.py` — Server module with multi-threaded connection handling and GUI
- `client.py` — Client module with GUI and server communication logic
- `CS408_Project_Fall24.pdf` — Original project specification

## Running the Application

**Start the server:**
```bash
python server.py
```
1. Browse and select a storage directory
2. Enter a port number (1024–65535)
3. Click "Start Server"

**Start a client (in a separate terminal):**
```bash
python client.py
```
1. Enter server IP, port, and a unique username
2. Click "Connect"
3. Use the GUI to upload, download, list, or delete files

> **Note:** This project handles ASCII text files only, as per the project specification.

## Key Concepts Demonstrated

- TCP socket programming (client-server model)
- Multi-threading for concurrent connection handling
- GUI development with tkinter
- Inter-process communication via custom protocols
- File I/O with chunked transfer for large files
- Persistent state management (JSON-based metadata)
- Graceful error handling and resource cleanup
