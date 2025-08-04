# Amazon Linux 2023 Development Environment Setup

This Ansible playbook recreates the complete development environment found on your Amazon Linux 2023 system.

---

# Virtual Microphone Setup

This directory also contains everything needed to set up a virtual microphone that loops prerecorded audio.

## Quick Start

### Shell Script (Original)
```bash
# Run the playbook (uses speech.wav by default)
./virtual-mic-playbook.sh

# Or specify your own audio file
./virtual-mic-playbook.sh your-audio.wav
```

### Ansible Playbook

**Main Playbook (includes virtual microphone setup):**
```bash
# Run the complete development environment setup (includes virtual microphone)
ansible-playbook -i inventory.yml playbook.yml

# Run with custom audio file
ansible-playbook -i inventory.yml playbook.yml -e audio_file_name=your-audio.wav
```

**Standalone Virtual Microphone Playbook:**
```bash
# Run only the virtual microphone setup
ansible-playbook -i inventory.yml virtual-mic-playbook.yml

# Or run locally
ansible-playbook -i "localhost," virtual-mic-playbook.yml --connection=local

# Specify custom audio file
ansible-playbook -i inventory.yml virtual-mic-playbook.yml -e audio_file_name=your-audio.wav
```

## What it does

1. **Installs** required audio packages (PulseAudio, ALSA)
2. **Creates** virtual speaker and microphone devices  
3. **Loops** your audio file through the virtual microphone
4. **Provides** a virtual mic that any recording tool can use

## Recording from Virtual Mic

```bash
# Record 20 seconds using arecord
arecord -D pulse -f cd -d 20 recording.wav

# Record using other tools
parecord --device=virtual_microphone output.wav
```

## Virtual Mic Files

- `roles/virtual-microphone/files/speech.wav` - Sample "one two three" audio file
- `virtual-mic-playbook.sh` - Original shell script setup
- `virtual-mic-playbook.yml` - Ansible playbook version
- `roles/virtual-microphone/` - Ansible role for virtual microphone setup
  - `tasks/main.yml` - Main automation tasks
  - `templates/virtual-mic-loop.sh.j2` - Audio loop script template
  - `vars/main.yml` - Default variables
  - `files/speech.wav` - Default audio file
- `virtual-mic-loop.sh` - Created by playbook to loop audio (in workspace)
- `virtual-mic-loop.log` - Audio loop process log (in workspace)

## Virtual Mic Cleanup

```bash
# Stop the virtual microphone
pkill -f virtual-mic-loop
pactl unload-module module-null-sink
pactl unload-module module-remap-source
```

---

## What This Playbook Installs

### Base System
- Essential system packages (curl, wget, vim, htop, etc.)
- Development Tools group (gcc, make, autotools, etc.)
- User configuration for `ec2-user` with sudo access

### Development Environment
- **Node.js v24.4.1** via NVM
- **Python 3.9.23** (system package)
- **Git 2.47.1**
- **Docker 25.0.8** with Docker Compose
- **Google Chrome** (stable)

### GUI/X11 Support
- Complete GTK3 development stack
- X11 libraries and development headers
- Mesa graphics drivers
- Font packages for proper rendering

### Applications
- **Google Chrome** (stable) with X11/GUI support
- **mosh**: Mobile shell (compiled from source)
- **certbot**: SSL certificate management with Route 53 DNS plugin
  - Automatic renewal (twice daily)
  - Monthly updates of certbot and plugins
- **dictate-cc**: Full-stack dictation application
- **test-web**: Chrome testing environment

### Virtual Microphone
- **PulseAudio** and **ALSA** audio utilities
- Virtual speaker and microphone devices for audio looping
- Automated audio file playback through virtual microphone
- Compatible with any recording software that can access system audio devices

## Usage

### 1. Setup Target Host
Ensure you have a fresh Amazon Linux 2023 instance with SSH access.

### 2. Configure Inventory
Edit `inventory.yml` and set:
```yaml
target_ip: "YOUR_EC2_INSTANCE_IP"
ssh_key_path: "PATH_TO_YOUR_SSH_KEY"
```

### 3. Run the Playbook

#### Install Ansible
```bash
# Install Ansible (if not already installed)
pip3 install ansible
```

#### Running Options

**Dry Run (Check Mode)** - Preview changes without making them:
```bash
# Full dry run
ansible-playbook -i inventory.yml playbook.yml --check --diff

# Dry run with specific tags
ansible-playbook -i inventory.yml playbook.yml --check --diff --tags "applications"
```

**Run Locally** - Execute on the current machine:
```bash
# Run on localhost (add connection: local to inventory)
ansible-playbook -i "localhost," playbook.yml --connection=local

# Or create local inventory file
echo "localhost ansible_connection=local" > local_inventory
ansible-playbook -i local_inventory playbook.yml
```

**Remote Execution** - Standard remote deployment:
```bash
# Run the complete setup (includes virtual microphone)
ansible-playbook -i inventory.yml playbook.yml

# Run specific parts only
ansible-playbook -i inventory.yml playbook.yml --tags "base,packages"
ansible-playbook -i inventory.yml playbook.yml --tags "development"
ansible-playbook -i inventory.yml playbook.yml --tags "docker"
ansible-playbook -i inventory.yml playbook.yml --tags "applications"
ansible-playbook -i inventory.yml playbook.yml --tags "virtual-microphone"

# Skip virtual microphone setup if not needed
ansible-playbook -i inventory.yml playbook.yml --skip-tags "virtual-microphone"
```

**Verbose Output** - For debugging:
```bash
# Verbose mode
ansible-playbook -i inventory.yml playbook.yml -v

# Extra verbose (shows task details)
ansible-playbook -i inventory.yml playbook.yml -vv

# Maximum verbosity (debug level)
ansible-playbook -i inventory.yml playbook.yml -vvv
```

### 4. Post-Installation
After running the playbook:

1. **Reboot the system** to ensure all group memberships take effect:
   ```bash
   sudo reboot
   ```

2. **Verify Node.js installation**:
   ```bash
   node --version  # Should show v24.4.1
   npm --version   # Should show 11.4.2
   ```

3. **Verify Docker access**:
   ```bash
   docker ps  # Should work without sudo
   ```

4. **Start applications** (if dictate-cc was successfully cloned):
   ```bash
   cd ~/workplace/dictate-cc
   docker-compose up -d
   ```

## Project Structure

```
.
├── playbook.yml         # Main playbook
├── inventory.yml        # Host configuration
├── group_vars/all.yml   # Variables
├── roles/
│   ├── base-system/
│   │   └── tasks/main.yml
│   ├── packages/
│   │   └── tasks/main.yml
│   ├── development/
│   │   └── tasks/main.yml
│   ├── docker/
│   │   └── tasks/main.yml
│   ├── applications/
│   │   └── tasks/
│   │       ├── main.yml      # Imports all app tasks
│   │       ├── chrome.yml    # Chrome installation
│   │       ├── mosh.yml      # Mosh compilation
│   │       └── certbot.yml   # SSL certificate management
│   └── virtual-microphone/
│       ├── tasks/main.yml    # Virtual microphone setup
│       ├── templates/virtual-mic-loop.sh.j2
│       ├── vars/main.yml
│       └── files/speech.wav  # Default audio file
├── run-playbook.sh      # Convenience script
└── virtual-mic-playbook.yml # Virtual microphone standalone playbook
```

## Directory Structure After Installation

```
/home/ec2-user/workplace/
├── dictate-cc/          # Full-stack dictation app
│   ├── backend/         # Node.js/TypeScript backend
│   ├── frontend/        # React frontend
│   ├── ssl/             # SSL certificates
│   └── docker-compose.yml
├── mosh/                # Mobile shell source
├── test-web/            # Chrome testing environment
└── ansible-setup/      # This playbook

/opt/certbot/            # Certbot virtual environment
├── bin/certbot          # Certbot executable
└── lib/python3.9/site-packages/  # Python packages
```

## Services and Ports

The system will have these services running:
- **SSH**: Port 22
- **HTTP**: Port 80
- **App Frontend**: Port 3000
- **App Backend**: Port 3001  
- **HTTPS Alt**: Port 3443
- **PostgreSQL**: Port 5432
- **Test Server**: Port 8080

## SSL Certificate Management

Certbot is configured with automatic renewal and Route 53 DNS validation:

### Automatic Renewal
- Runs twice daily (midnight and noon) with random delay
- Uses DNS validation for wildcard certificates
- Logs to `/var/log/certbot/`

### Monthly Updates
- Certbot and plugins are automatically updated on the 1st of each month
- Includes certbot-dns-route53 and certbot-nginx plugins

### Manual Certificate Operations
```bash
# Request a wildcard certificate
sudo certbot certonly --dns-route53 -d example.com -d '*.example.com'

# Test renewal
sudo certbot renew --dry-run

# Check certificate status
sudo certbot certificates
```

## Customization

### Adding Your Own Applications
1. Create a new task file in `roles/applications/tasks/your-app.yml`
2. Add your tasks with appropriate tags
3. Import the task file in `roles/applications/tasks/main.yml`

Example:
```yaml
# roles/applications/tasks/your-app.yml
---
- name: Install your application
  package:
    name: your-app
    state: present
  tags: applications
```

Then add to `roles/applications/tasks/main.yml`:
```yaml
- import_tasks: your-app.yml
```

### Modifying Package Lists
Edit `roles/packages/tasks/main.yml` to add or remove packages.

### Changing Node.js Version
Update the `node_version` variable in `group_vars/all.yml`.

## Troubleshooting

### Chrome Won't Start
Ensure all X11 packages were installed:
```bash
google-chrome --version
```

### Docker Permission Issues
Re-login or reboot after installation to refresh group memberships.

### Mosh Compilation Fails
Check that all development dependencies are installed:
```bash
dnf groupinfo "Development Tools"
```

### Certbot Issues
Check the virtual environment and symlink:
```bash
# Verify certbot installation
/opt/certbot/bin/certbot --version

# Check symlink
ls -la /usr/local/bin/certbot

# View renewal logs
sudo tail -f /var/log/certbot/renewal.log
```

### DNS Route 53 Authentication
For Route 53 DNS validation, ensure AWS credentials are configured:
```bash
# Using AWS CLI
aws configure

# Or environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

## Security Notes

- The playbook generates self-signed SSL certificates for development use
- Docker daemon is configured with log rotation
- SSH access remains configured as per EC2 defaults
- No firewall rules are modified - configure as needed for your environment

## License

This playbook is provided as-is for educational and development purposes.