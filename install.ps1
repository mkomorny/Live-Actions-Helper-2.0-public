$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bridge = Join-Path $root "bridge"
$dest = "A:\User Library\Presets\Audio Effects\Max Audio Effect\Live Actions"
$old = @(
    "A:\User Library\Presets\MIDI Effects\Max MIDI Effect\Live Actions Bridge",
    "A:\User Library\Presets\MIDI Effects\Max MIDI Effect\Live Actions MIDI",
    "A:\User Library\Presets\Audio Effects\Max Audio Effect\Live Actions Audio"
)
$desktop = [Environment]::GetFolderPath("Desktop")

New-Item -ItemType Directory -Force -Path $dest | Out-Null
python (Join-Path $bridge "pack-amxd.py")

# Stamp a fresh build id into the DEPLOYED copy only -- the repo source keeps
# the "dev" placeholder. This lets Verify-BridgeDeploy (below) tell a freshly
# re-dropped device apart from a stale one still running yesterday's JS: Max
# only reloads live-actions-bridge.js when the device is removed and
# re-added to a track, not just because the file on disk changed.
$buildId = Get-Date -Format "yyyyMMddTHHmmss"
# Read as UTF-8 explicitly -- Windows PowerShell 5.1's default Get-Content
# encoding is the system ANSI codepage, not UTF-8, so a plain -Raw read here
# corrupted any non-ASCII character (e.g. the "-" in Detect Key's dashes) on
# the way in, and [IO.File]::WriteAllText below avoids re-corrupting them (and
# avoids Set-Content's UTF-8-with-BOM) on the way back out (M8).
$bridgeJs = Get-Content (Join-Path $bridge "live-actions-bridge.js") -Raw -Encoding UTF8
$bridgeJs = $bridgeJs -replace 'var BRIDGE_BUILD = "[^"]*";', "var BRIDGE_BUILD = `"$buildId`";"
$destBridgeJsPath = Join-Path $dest "live-actions-bridge.js"
[IO.File]::WriteAllText($destBridgeJsPath, $bridgeJs, (New-Object Text.UTF8Encoding $false))

Copy-Item -Force (Join-Path $bridge "live-actions-pal.js") $dest
Copy-Item -Force (Join-Path $bridge "Live Actions Bridge.maxpat") $dest
Copy-Item -Force (Join-Path $bridge "Live Actions Bridge.amxd") (Join-Path $dest "Live Actions.amxd")
$launchBat = Join-Path $root "Launch Live Actions.bat"
Set-Content -Path (Join-Path $dest "host-path.txt") -Value $launchBat -Encoding ascii
foreach ($path in $old) {
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path
        Write-Output "Removed split device folder: $path"
    }
}
Copy-Item -Force (Join-Path $root "HOW-TO-START.txt") (Join-Path $desktop "Live Actions - how to start.txt")

# ---- Engine E2: the LiveActionsRS browser Remote Script -----------------------
# Live's browser (the library panel on the left) is not in the Max for Live LOM
# at all -- probed live in v1.0.34, `live_app browser` returned exists:false with
# 0 children. Application.browser only exists inside a MIDI Remote Script, so
# the browser tools talk to this instead of the OSC bridge.
#
# Installed into the User Library rather than
# C:\ProgramData\Ableton\Live 12*\Resources\MIDI Remote Scripts: no admin rights
# needed, and a Live update cannot wipe it.
$rsSrc = Join-Path $root "remote_script\LiveActionsRS"
$rsDest = "A:\User Library\Remote Scripts\LiveActionsRS"
if (Test-Path $rsSrc) {
    New-Item -ItemType Directory -Force -Path $rsDest | Out-Null
    Copy-Item -Force (Join-Path $rsSrc "__init__.py") $rsDest
    Write-Output "Installed browser engine (LiveActionsRS) to $rsDest"
} else {
    Write-Warning "remote_script\LiveActionsRS not found -- browser tools will stay unavailable."
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $desktop "Live Actions.lnk"))
$shortcut.TargetPath = Join-Path $root "Launch Live Actions.bat"
$shortcut.WorkingDirectory = $root
$shortcut.WindowStyle = 7
$shortcut.Description = "Live Actions desktop host"
$shortcut.Save()

# Windows reports "this file does not have an app associated with it" when the
# protocol command names an exe that is not there. Get-Command hits the 0-byte
# WindowsApps alias first, and the old fallback was Python 3.12 under
# %LOCALAPPDATA%\Programs\Python, which is gone on this PC. Prefer a real file.
function Resolve-Pythonw {
    $candidates = New-Object System.Collections.Generic.List[string]
    $candidates.Add((Join-Path $env:LOCALAPPDATA "Python\bin\pythonw.exe"))
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        foreach ($line in @(& $py.Source -0p 2>$null)) {
            if ($line -match '([A-Za-z]:\\.+\\python\.exe)\s*$') {
                $candidates.Add(($Matches[1] -replace '\\python\.exe$','\pythonw.exe'))
            }
        }
    }
    foreach ($cmd in @(Get-Command pythonw.exe -All -ErrorAction SilentlyContinue)) {
        $candidates.Add($cmd.Source)
    }
    foreach ($path in $candidates) {
        if (-not $path -or -not (Test-Path -LiteralPath $path)) { continue }
        if ((Get-Item -LiteralPath $path).Length -lt 10000) { continue }
        return (Get-Item -LiteralPath $path).FullName
    }
    throw "No real pythonw.exe found. Install Python, then run this script again. A Windows Store alias is not enough for liveactions://"
}
$pythonw = Resolve-Pythonw
$helper = Join-Path $root "app\shell.py"
$proto = "HKCU:\Software\Classes\liveactions"
New-Item -Path $proto -Force | Out-Null
Set-ItemProperty -Path $proto -Name "(default)" -Value "URL:Live Actions Protocol"
New-ItemProperty -Path $proto -Name "URL Protocol" -Value "" -Force | Out-Null
New-Item -Path "$proto\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path "$proto\shell\open\command" -Name "(default)" -Value ("`"{0}`" `"{1}`" `"%1`"" -f $pythonw, $helper)
Write-Output "URL protocol handler: $pythonw"

Write-Output "Installed Live Actions device to $dest"
Write-Output "Desktop shortcut: Live Actions.lnk"
Write-Output "URL protocol: liveactions://open"

# Confirm the device actually running in Live picked up this build. Copying
# the file is not enough by itself -- Max only reloads live-actions-bridge.js
# when the device is removed and re-dropped on a track, so a device that was
# already sitting on a track before this install will keep running its old,
# in-memory copy of the script until you re-drop it.
function Test-BridgeBuild {
    param([string]$ExpectedBuild, [int]$SendPort = 11924, [int]$ListenPort = 11925, [int]$TimeoutMs = 2500)
    $listener = $null
    $sender = $null
    try {
        $sock = New-Object System.Net.Sockets.Socket([System.Net.Sockets.AddressFamily]::InterNetwork, [System.Net.Sockets.SocketType]::Dgram, [System.Net.Sockets.ProtocolType]::Udp)
        $sock.SetSocketOption([System.Net.Sockets.SocketOptionLevel]::Socket, [System.Net.Sockets.SocketOptionName]::ReuseAddress, $true)
        $sock.Bind((New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Parse("127.0.0.1"), $ListenPort)))
        $listener = New-Object System.Net.Sockets.UdpClient
        $listener.Client = $sock
        $listener.Client.ReceiveTimeout = $TimeoutMs

        $addrBytes = [System.Text.Encoding]::UTF8.GetBytes("/live-actions/ping" + "`0")
        $addrBytes += New-Object byte[] ((4 - ($addrBytes.Length % 4)) % 4)
        $tagBytes = [System.Text.Encoding]::UTF8.GetBytes("," + "`0")
        $tagBytes += New-Object byte[] ((4 - ($tagBytes.Length % 4)) % 4)
        $msg = $addrBytes + $tagBytes

        $sender = New-Object System.Net.Sockets.UdpClient
        $sender.Send($msg, $msg.Length, "127.0.0.1", $SendPort) | Out-Null

        $remote = New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Any, 0)
        $deadline = (Get-Date).AddMilliseconds($TimeoutMs)
        while ((Get-Date) -lt $deadline) {
            $data = $listener.Receive([ref]$remote)
            $nul = [Array]::IndexOf($data, [byte]0)
            if ($nul -lt 0) { continue }
            $recvAddr = [System.Text.Encoding]::UTF8.GetString($data, 0, $nul)
            if ($recvAddr -ne "/live-actions/pong") { continue }
            $off = [Math]::Ceiling(($nul + 1) / 4.0) * 4
            $tagNul = [Array]::IndexOf($data, [byte]0, $off)
            $off = [Math]::Ceiling(($tagNul + 1) / 4.0) * 4
            $argNul = [Array]::IndexOf($data, [byte]0, $off)
            $json = [System.Text.Encoding]::UTF8.GetString($data, $off, $argNul - $off)
            $info = $json | ConvertFrom-Json
            return $info.build
        }
        return $null
    } catch {
        Write-Host "  (bridge check error: $($_.Exception.Message))"
        return $null
    } finally {
        if ($listener) { $listener.Close() }
        if ($sender) { $sender.Close() }
    }
}

Write-Output ""
Write-Output "Checking whether the device running in Live is this build..."
$runningBuild = Test-BridgeBuild -ExpectedBuild $buildId
if (-not $runningBuild) {
    Write-Output "Could not reach the bridge (Live may not be running, the device isn't on a track yet, or the desktop app has port 11925 open right now). Nothing to verify this run."
} elseif ($runningBuild -eq $buildId) {
    Write-Output "Confirmed: the device running in Live is this build ($buildId)."
} else {
    Write-Output ""
    Write-Output "*** The device running in Live is STALE (build $runningBuild, expected $buildId). ***"
    Write-Output "*** Remove 'Live Actions Bridge' from its track in Live and drag it back on to pick up the new code. ***"
    Write-Output ""
}

# ---- Engine E2 reachability -------------------------------------------------
# Copying the script is not enough: a Remote Script only loads once it is
# selected as a Control Surface, and that takes a Live restart. Say so plainly
# rather than letting the browser tools look broken later.
Write-Output ""
Write-Output "Checking whether the browser engine (LiveActionsRS) is running..."
$rsOk = $false
try {
    $client = New-Object System.Net.Sockets.TcpClient
    $iar = $client.BeginConnect("127.0.0.1", 11926, $null, $null)
    if ($iar.AsyncWaitHandle.WaitOne(1500) -and $client.Connected) {
        $client.EndConnect($iar)
        $stream = $client.GetStream()
        $payload = [System.Text.Encoding]::UTF8.GetBytes('{"id":1,"action":"ping","params":{}}' + "`n")
        $stream.Write($payload, 0, $payload.Length)
        $stream.ReadTimeout = 3000
        $buf = New-Object byte[] 8192
        $n = $stream.Read($buf, 0, $buf.Length)
        if ($n -gt 0 -and [System.Text.Encoding]::UTF8.GetString($buf, 0, $n) -match '"ok"\s*:\s*true') { $rsOk = $true }
    }
    $client.Close()
} catch { }
if ($rsOk) {
    Write-Output "Confirmed: the browser engine is answering on port 11926 -- Genius can read and load from Live's browser."
} else {
    Write-Output ""
    Write-Output "*** The browser engine is NOT running. Genius will work, but cannot browse, audition or load presets/plug-ins. ***"
    Write-Output '*** In Live: Preferences > Link/Tempo/MIDI, set a free Control Surface slot to "LiveActionsRS", then restart Live. ***'
    Write-Output ""
}
