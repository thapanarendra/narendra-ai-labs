# 🏢 OrgChart Creator Pro

A powerful, modern organizational chart builder with a beautiful UI. Create, customize, and export professional org charts in minutes — no account required, works entirely in your browser.

![OrgChart Creator Pro](https://img.shields.io/badge/Version-2.0-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![JavaScript](https://img.shields.io/badge/JavaScript-Vanilla-yellow) ![Platform](https://img.shields.io/badge/Platform-Web-orange)

## 📋 Table of Contents

- [Features](#-features)
- [Demo](#-demo)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Keyboard Shortcuts](#️-keyboard-shortcuts)
- [CSV Import Format](#-csv-import-format)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 📊 Core Features
- **Drag & Drop Interface** — Freely position nodes anywhere on the infinite canvas
- **Multiple Charts** — Create and manage multiple org charts with easy switching
- **Auto-Save** — Your work is automatically saved to browser localStorage
- **Responsive Design** — Works on desktop, tablet, and mobile devices
- **Auto Layout** — Automatically arrange nodes in a hierarchical tree structure

### 🎨 Visual Customization
- **Custom Card Colors** — Personalize individual card colors or set defaults
- **Custom Line Colors** — Change connection line and arrow colors
- **Profile Photos** — Add photos to team members via drag & drop or upload
- **Company Logo** — Upload company logos for each chart

### 🔍 Navigation & Organization
- **Minimap** — Bird's-eye view for navigating large charts
- **Zoom Controls** — Zoom in/out with buttons, scroll wheel, or keyboard
- **Grid Snap** — Align nodes to a grid for cleaner layouts
- **Fit All** — Auto-fit all nodes in the viewport
- **Center View** — Quickly center the chart

### 🔗 Connections & Hierarchy
- **Smart Connections** — Create manager/report/peer relationships
- **Report Count Badges** — See direct report counts on each card
- **Multi-Directional** — Connect nodes from any direction (top, bottom, left, right)

### ⌨️ Productivity
- **Keyboard Navigation** — Navigate between nodes with arrow keys
- **Keyboard Shortcuts** — Efficient workflow with hotkeys
- **Multi-Select** — Select multiple nodes with Shift+Click or rubber band selection
- **Copy/Paste** — Duplicate nodes instantly
- **Undo/Redo** — Full history support
- **Built-in Tips** — Quick help guide in the sidebar

### 📤 Import & Export
- **Import from CSV** — Bulk import people with automatic hierarchy creation
- **Download Sample CSV** — Get a template CSV to start quickly
- **Export as JSON** — Data backup and transfer

## 🎬 Demo

Simply open `index.html` in any modern browser to start using OrgChart Creator Pro. No installation required!

## 📦 Requirements

### Minimum Requirements
- A modern web browser (Chrome, Firefox, Safari, Edge)
- That's it! No server, database, or dependencies required for basic usage.

### For Local Development Server (Recommended)
You only need ONE of the following to run a local server:

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.x | Built-in HTTP server |
| Node.js | 14+ | npx serve or http-server |
| PHP | 7+ | Built-in HTTP server |

## 🚀 Installation

### Option 1: Direct Download (Simplest)

1. Download or clone this repository
2. Open `index.html` directly in your browser
3. Start creating!

```bash
# Clone the repository
git clone https://github.com/thapanarendra/narendra-ai-labs.git

# Navigate to the folder
cd narendra-ai-labs

# Open in browser (varies by OS, see below)
```

### Option 2: Local Development Server (Recommended)

Running a local server enables better performance and avoids potential browser security restrictions.

---

#### 🍎 macOS

**Using Python (pre-installed on macOS):**
```bash
# Navigate to project folder
cd /path/to/orgchart-creator-pro

# Start server with Python 3
python3 -m http.server 8080

# Open in browser
open http://localhost:8080
```

**Using Node.js:**
```bash
# Install Node.js via Homebrew (if not installed)
brew install node

# Navigate to project folder
cd /path/to/orgchart-creator-pro

# Option A: Using npx (no install needed)
npx serve .

# Option B: Using http-server
npm install -g http-server
http-server -p 8080

# Open in browser
open http://localhost:8080
```

**Using PHP (if installed):**
```bash
# Navigate to project folder
cd /path/to/orgchart-creator-pro

# Start PHP built-in server
php -S localhost:8080

# Open in browser
open http://localhost:8080
```

---

#### 🐧 Linux (Ubuntu/Debian)

**Using Python:**
```bash
# Install Python 3 (if not installed)
sudo apt update
sudo apt install python3

# Navigate to project folder
cd /path/to/orgchart-creator-pro

# Start server
python3 -m http.server 8080

# Open in browser
xdg-open http://localhost:8080
# Or manually open http://localhost:8080 in your browser
```

**Using Node.js:**
```bash
# Install Node.js (if not installed)
sudo apt update
sudo apt install nodejs npm

# Navigate to project folder
cd /path/to/orgchart-creator-pro

# Option A: Using npx
npx serve .

# Option B: Using http-server
npm install -g http-server
http-server -p 8080

# Open in browser
xdg-open http://localhost:8080
```

**Using PHP:**
```bash
# Install PHP (if not installed)
sudo apt update
sudo apt install php

# Navigate to project folder
cd /path/to/orgchart-creator-pro

# Start PHP built-in server
php -S localhost:8080

# Open in browser
xdg-open http://localhost:8080
```

---

#### 🪟 Windows

**Using Python:**
```powershell
# Install Python from https://www.python.org/downloads/
# Make sure to check "Add Python to PATH" during installation

# Open Command Prompt or PowerShell
# Navigate to project folder
cd C:\path\to\orgchart-creator-pro

# Start server
python -m http.server 8080

# Open in browser
start http://localhost:8080
```

**Using Node.js:**
```powershell
# Install Node.js from https://nodejs.org/

# Open Command Prompt or PowerShell
# Navigate to project folder
cd C:\path\to\orgchart-creator-pro

# Option A: Using npx
npx serve .

# Option B: Using http-server
npm install -g http-server
http-server -p 8080

# Open in browser
start http://localhost:8080
```

**Using PHP:**
```powershell
# Install PHP from https://windows.php.net/download/
# Add PHP to your system PATH

# Open Command Prompt or PowerShell
# Navigate to project folder
cd C:\path\to\orgchart-creator-pro

# Start PHP built-in server
php -S localhost:8080

# Open in browser
start http://localhost:8080
```

**Using Visual Studio Code Live Server:**
```
1. Install VS Code from https://code.visualstudio.com/
2. Install "Live Server" extension
3. Open the project folder in VS Code
4. Right-click on index.html → "Open with Live Server"
```

---

### Quick Reference: Server Commands

| OS | Python | Node.js | PHP |
|----|--------|---------|-----|
| **macOS** | `python3 -m http.server 8080` | `npx serve .` | `php -S localhost:8080` |
| **Linux** | `python3 -m http.server 8080` | `npx serve .` | `php -S localhost:8080` |
| **Windows** | `python -m http.server 8080` | `npx serve .` | `php -S localhost:8080` |

## 📖 Usage

### Creating Your First Chart

1. On the welcome page, enter your **company/account name**
2. Optionally upload a company logo
3. Click **"Create New Chart"**

Or click **"Open Saved Charts"** to load previously saved charts.

### Adding Team Members

1. Click **"Add Person"** dropdown in the toolbar
2. Fill in the member details (name, title, email, phone)
3. Optionally add a profile photo and set a card color
4. Click **"Add Member"**

### Building the Hierarchy

- **Hover** over any member card to see the action buttons
- Click the directional arrows to add:
  - ⬆️ **Above** - Add a manager
  - ⬇️ **Below** - Add a direct report
  - ⬅️ **Left** - Add a peer (sibling)
  - ➡️ **Right** - Add a peer (sibling)

### Multi-Select & Move

1. **Shift+Click** or **Ctrl+Click** to select multiple nodes
2. Or **click and drag** on empty space to draw a selection box
3. Drag any selected node to move all selected nodes together

### Exporting

- Use the **Export** dropdown for JSON export (data backup/transfer)
- Use **Import from CSV** in the sidebar to bulk import people

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `↑` `↓` `←` `→` | Navigate between nodes |
| `Enter` | Edit selected node |
| `Delete` / `Backspace` | Delete selected nodes |
| `Escape` | Clear selection / Close modals |
| `Ctrl/Cmd + A` | Select all nodes |
| `Ctrl/Cmd + C` | Copy selected nodes |
| `Ctrl/Cmd + V` | Paste nodes |
| `Ctrl/Cmd + Z` | Undo |
| `Ctrl/Cmd + Y` | Redo |
| `Ctrl/Cmd + S` | Save chart |
| `+` / `=` | Zoom in |
| `-` | Zoom out |
| `0` | Reset zoom to 100% |
| `F` | Fit all nodes to view |
| `G` | Toggle grid snap |
| `?` | Show keyboard shortcuts |

## 📁 CSV Import Format

Import your org data from a CSV file with these columns:

```csv
Name,Designation,Manager,Email,Phone,Department,Location
John Smith,CEO,,john@company.com,+1-555-0100,Executive,New York
Jane Doe,CTO,John Smith,jane@company.com,+1-555-0101,Engineering,San Francisco
Bob Wilson,VP Engineering,Jane Doe,bob@company.com,+1-555-0102,Engineering,Austin
```

| Column | Required | Description |
|--------|----------|-------------|
| **Name** | ✅ Yes | Person's full name |
| **Designation** | ✅ Yes | Job title |
| **Manager** | No | Name of the person's manager (creates connection) |
| **Email** | No | Email address |
| **Phone** | No | Phone number |
| **Department** | No | Department name |
| **Location** | No | Office location |

> 💡 **Tip:** Click "Download Sample CSV" in the sidebar to get a ready-to-use template!

## 🛠️ Tech Stack

- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **Libraries**: 
  - [html2canvas](https://html2canvas.hertzen.com/) — Image export
  - [Font Awesome 6](https://fontawesome.com/) — Icons
  - [Google Fonts (Inter)](https://fonts.google.com/specimen/Inter) — Typography
- **Storage**: localStorage (browser-based, no server required)
- **No Build Tools Required** — Just HTML, CSS, and JavaScript

## 📂 Project Structure

```
orgchart-creator-pro/
├── index.html      # Main HTML structure
├── styles.css      # All styles (~2400 lines)
├── app.js          # Application logic (~2700 lines)
├── sample.csv      # Sample CSV template for import
├── README.md       # Documentation
└── LICENSE         # MIT License
```

## 🎯 Use Cases

- **HR Teams** — Visualize company structure
- **Managers** — Plan team reorganizations
- **Recruiters** — Show org structure to candidates
- **Consultants** — Document client organizations
- **Startups** — Plan team growth

## 🔒 Privacy

OrgChart Creator Pro runs entirely in your browser:
- ✅ No data sent to servers
- ✅ No account required
- ✅ No tracking or analytics
- ✅ All data stored locally in your browser
- ✅ Works offline after initial load

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Ways to Contribute
- 🐛 Report bugs by opening an issue
- 💡 Suggest features or improvements
- 📖 Improve documentation
- 🔧 Submit pull requests

### Development Workflow
```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/narendra-ai-labs.git
cd narendra-ai-labs

# 3. Create a feature branch
git checkout -b feature/amazing-feature

# 4. Make your changes and test locally
python3 -m http.server 8080

# 5. Commit your changes
git add .
git commit -m "Add amazing feature"

# 6. Push to your fork
git push origin feature/amazing-feature

# 7. Open a Pull Request on GitHub
```

### Code Style Guidelines
- Use vanilla JavaScript (ES6+)
- Follow existing code formatting
- Comment complex logic
- Test on multiple browsers

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 🙏 Acknowledgments

- Icons by [Font Awesome](https://fontawesome.com/)
- Font by [Google Fonts](https://fonts.google.com/)
- Image export by [html2canvas](https://html2canvas.hertzen.com/)

## 📞 Support

- 🐛 **Bug Reports**: [Open an issue](https://github.com/thapanarendra/narendra-ai-labs/issues)
- 💬 **Questions**: [Discussions](https://github.com/thapanarendra/narendra-ai-labs/discussions)
- ⭐ **Like this project?** Give it a star!

---

<p align="center">
  Made with ❤️ for teams everywhere
</p>

Made with ❤️ for teams everywhere

**⭐ Star this repo if you find it useful!**
