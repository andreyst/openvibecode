#!/bin/bash

# Virtual Microphone Setup Playbook
# Assumes you have an audio file ready (speech.wav)

set -e

AUDIO_FILE="${1:-speech.wav}"
VIRTUAL_SPEAKER="virtual_speaker"
VIRTUAL_MIC="virtual_microphone"

echo "🎤 Virtual Microphone Setup Playbook"
echo "======================================"

# Check if audio file exists
if [ ! -f "$AUDIO_FILE" ]; then
    echo "❌ Error: Audio file '$AUDIO_FILE' not found!"
    echo "Usage: $0 [audio_file.wav]"
    exit 1
fi

echo "📁 Audio file: $AUDIO_FILE"

# Step 1: Install required packages
echo "📦 Step 1: Installing required packages..."
if command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y pulseaudio-utils alsa-utils alsa-plugins-pulseaudio
elif command -v apt >/dev/null 2>&1; then
    sudo apt update && sudo apt install -y pulseaudio-utils alsa-utils
else
    echo "⚠️  Warning: Unknown package manager. Please install pulseaudio-utils and alsa-utils manually."
fi

# Step 2: Clean up any existing virtual devices
echo "🧹 Step 2: Cleaning up existing virtual devices..."
pactl unload-module module-null-sink 2>/dev/null || true
pactl unload-module module-remap-source 2>/dev/null || true
pkill -f "virtual-mic-loop" 2>/dev/null || true

# Step 3: Create virtual audio devices
echo "🔧 Step 3: Creating virtual audio devices..."
SINK_MODULE=$(pactl load-module module-null-sink sink_name=$VIRTUAL_SPEAKER sink_properties=device.description="Virtual_Speaker")
echo "   Created virtual speaker (module $SINK_MODULE)"

SOURCE_MODULE=$(pactl load-module module-remap-source master=$VIRTUAL_SPEAKER.monitor source_name=$VIRTUAL_MIC source_properties=device.description="Virtual_Microphone")
echo "   Created virtual microphone (module $SOURCE_MODULE)"

# Step 4: Create audio loop script
echo "📝 Step 4: Creating audio loop script..."
cat > virtual-mic-loop.sh << EOF
#!/bin/bash
echo "🔄 Starting audio loop for virtual microphone..."
while true; do
    paplay --device=$VIRTUAL_SPEAKER "$AUDIO_FILE"
    sleep 0.5
done
EOF

chmod +x virtual-mic-loop.sh

# Step 5: Start audio loop
echo "▶️  Step 5: Starting audio loop..."
nohup ./virtual-mic-loop.sh > virtual-mic-loop.log 2>&1 &
LOOP_PID=$!
echo "   Audio loop started (PID: $LOOP_PID)"

# Wait for audio to start
sleep 3

# Step 6: Verify setup
echo "✅ Step 6: Verifying setup..."
echo "Available audio sources:"
pactl list sources short | grep -E "(virtual|Virtual)" || echo "   No virtual sources found"

echo ""
echo "🎉 Virtual Microphone Setup Complete!"
echo "======================================"
echo "📋 Summary:"
echo "   • Virtual speaker: $VIRTUAL_SPEAKER"
echo "   • Virtual microphone: $VIRTUAL_MIC"
echo "   • Audio file: $AUDIO_FILE"
echo "   • Loop process PID: $LOOP_PID"
echo ""
echo "🔧 Usage:"
echo "   # Record 20 seconds from virtual mic:"
echo "   arecord -D pulse -f cd -d 20 test-recording.wav"
echo ""
echo "   # List audio devices:"
echo "   pactl list sources short"
echo ""
echo "🛑 To stop:"
echo "   pkill -f virtual-mic-loop"
echo "   pactl unload-module $SINK_MODULE"
echo "   pactl unload-module $SOURCE_MODULE"
echo ""