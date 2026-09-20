const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow() {
  const window = new BrowserWindow({
    width: 1360, height: 860, minWidth: 980, minHeight: 640,
    backgroundColor: '#f7f8fc',
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  })
  const devUrl = process.env.VITE_DEV_SERVER_URL || 'http://localhost:5173'
  window.loadURL(devUrl).catch(() => window.loadFile(path.join(__dirname, '../dist/index.html')))
}
app.whenReady().then(createWindow)
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
