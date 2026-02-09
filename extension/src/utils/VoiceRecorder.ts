/**
 * VoiceRecorder — Records microphone audio from the extension host
 * using Windows' built-in MCI (winmm.dll) via PowerShell.
 *
 * VS Code webviews block navigator.mediaDevices.getUserMedia,
 * so we record on the Node.js side instead.
 */
import { ChildProcess, spawn } from 'child_process';
import { existsSync, readFileSync, unlinkSync, writeFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

export class VoiceRecorder {
    private process: ChildProcess | null = null;
    private wavPath: string;
    private stopPath: string;
    private scriptPath: string;
    private recording = false;

    constructor() {
        const stamp = Date.now();
        const tmp = tmpdir();
        this.wavPath = join(tmp, `idolcode_voice_${stamp}.wav`);
        this.stopPath = join(tmp, `idolcode_stop_${stamp}.flag`);
        this.scriptPath = join(tmp, `idolcode_rec_${stamp}.ps1`);
    }

    /** Start recording from the default microphone */
    start(): void {
        if (this.recording) { return; }
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

        writeFileSync(this.scriptPath, script, 'utf-8');

        this.process = spawn('powershell.exe', [
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', this.scriptPath
        ], { stdio: 'ignore', windowsHide: true });

        this.recording = true;
        console.log('🎙️ VoiceRecorder: recording started');
    }

    /** Stop recording and return Base64-encoded WAV data */
    async stop(): Promise<string> {
        if (!this.recording) { throw new Error('Not recording'); }
        this.recording = false;

        // Signal the PowerShell script to stop
        writeFileSync(this.stopPath, 'stop');

        // Wait for the PowerShell process to exit
        await new Promise<void>(resolve => {
            const timeout = setTimeout(() => {
                this.process?.kill();
                resolve();
            }, 6000);

            if (this.process) {
                this.process.on('exit', () => {
                    clearTimeout(timeout);
                    resolve();
                });
            } else {
                clearTimeout(timeout);
                resolve();
            }
        });

        // Give a little time for the file to flush
        await new Promise(r => setTimeout(r, 300));

        // Read the WAV file and return as Base64
        if (existsSync(this.wavPath)) {
            const buffer = readFileSync(this.wavPath);
            console.log(`🎙️ VoiceRecorder: captured ${buffer.length} bytes`);
            this.cleanFiles();
            return buffer.toString('base64');
        }

        this.cleanFiles();
        throw new Error('Recording failed — no audio file produced');
    }

    get isRecording(): boolean {
        return this.recording;
    }

    private cleanFiles(): void {
        for (const f of [this.wavPath, this.stopPath, this.scriptPath]) {
            try { if (existsSync(f)) { unlinkSync(f); } } catch { /* ignore */ }
        }
    }

    dispose(): void {
        this.cleanFiles();
        if (this.process) {
            this.process.kill();
            this.process = null;
        }
    }
}
