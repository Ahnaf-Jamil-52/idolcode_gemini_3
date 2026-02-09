"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.VoiceRecorder = void 0;
/**
 * VoiceRecorder — Records microphone audio from the extension host
 * using Windows' built-in MCI (winmm.dll) via PowerShell.
 *
 * VS Code webviews block navigator.mediaDevices.getUserMedia,
 * so we record on the Node.js side instead.
 */
const child_process_1 = require("child_process");
const fs_1 = require("fs");
const path_1 = require("path");
const os_1 = require("os");
class VoiceRecorder {
    constructor() {
        this.process = null;
        this.recording = false;
        const stamp = Date.now();
        const tmp = (0, os_1.tmpdir)();
        this.wavPath = (0, path_1.join)(tmp, `idolcode_voice_${stamp}.wav`);
        this.stopPath = (0, path_1.join)(tmp, `idolcode_stop_${stamp}.flag`);
        this.scriptPath = (0, path_1.join)(tmp, `idolcode_rec_${stamp}.ps1`);
    }
    /** Start recording from the default microphone */
    start() {
        if (this.recording) {
            return;
        }
        this.cleanFiles();
        // Build PowerShell script that uses winmm.dll MCI to record audio
        const wavNorm = this.wavPath.replace(/\\/g, '/');
        const stopNorm = this.stopPath.replace(/\\/g, '/');
        const script = [
            'Add-Type -TypeDefinition @"',
            'using System;',
            'using System.Runtime.InteropServices;',
            'using System.Text;',
            'public class WinMCI {',
            '    [DllImport("winmm.dll", CharSet = CharSet.Unicode)]',
            '    public static extern int mciSendStringW(string command, StringBuilder buffer, int bufferSize, IntPtr callback);',
            '}',
            '"@',
            '',
            '$buf = New-Object System.Text.StringBuilder 512',
            `$wav = '${wavNorm}'`,
            `$sig = '${stopNorm}'`,
            '',
            "[WinMCI]::mciSendStringW('open new type waveaudio alias mic', $buf, 512, [IntPtr]::Zero) | Out-Null",
            "[WinMCI]::mciSendStringW('record mic', $buf, 512, [IntPtr]::Zero) | Out-Null",
            '',
            '# Poll for stop signal (max 30 seconds)',
            '$t = 0',
            'while ((-not (Test-Path $sig)) -and ($t -lt 30000)) {',
            '    Start-Sleep -Milliseconds 200',
            '    $t += 200',
            '}',
            '',
            '# Save and close',
            '[WinMCI]::mciSendStringW("save mic `"$wav`"", $buf, 512, [IntPtr]::Zero) | Out-Null',
            "[WinMCI]::mciSendStringW('close mic', $buf, 512, [IntPtr]::Zero) | Out-Null",
            'if (Test-Path $sig) { Remove-Item $sig -Force }',
        ].join('\r\n');
        (0, fs_1.writeFileSync)(this.scriptPath, script, 'utf-8');
        this.process = (0, child_process_1.spawn)('powershell.exe', [
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', this.scriptPath
        ], { stdio: 'ignore', windowsHide: true });
        this.recording = true;
        console.log('🎙️ VoiceRecorder: recording started');
    }
    /** Stop recording and return Base64-encoded WAV data */
    async stop() {
        if (!this.recording) {
            throw new Error('Not recording');
        }
        this.recording = false;
        // Signal the PowerShell script to stop
        (0, fs_1.writeFileSync)(this.stopPath, 'stop');
        // Wait for the PowerShell process to exit
        await new Promise(resolve => {
            const timeout = setTimeout(() => {
                this.process?.kill();
                resolve();
            }, 6000);
            if (this.process) {
                this.process.on('exit', () => {
                    clearTimeout(timeout);
                    resolve();
                });
            }
            else {
                clearTimeout(timeout);
                resolve();
            }
        });
        // Give a little time for the file to flush
        await new Promise(r => setTimeout(r, 300));
        // Read the WAV file and return as Base64
        if ((0, fs_1.existsSync)(this.wavPath)) {
            const buffer = (0, fs_1.readFileSync)(this.wavPath);
            console.log(`🎙️ VoiceRecorder: captured ${buffer.length} bytes`);
            this.cleanFiles();
            return buffer.toString('base64');
        }
        this.cleanFiles();
        throw new Error('Recording failed — no audio file produced');
    }
    get isRecording() {
        return this.recording;
    }
    cleanFiles() {
        for (const f of [this.wavPath, this.stopPath, this.scriptPath]) {
            try {
                if ((0, fs_1.existsSync)(f)) {
                    (0, fs_1.unlinkSync)(f);
                }
            }
            catch { /* ignore */ }
        }
    }
    dispose() {
        this.cleanFiles();
        if (this.process) {
            this.process.kill();
            this.process = null;
        }
    }
}
exports.VoiceRecorder = VoiceRecorder;
//# sourceMappingURL=VoiceRecorder.js.map