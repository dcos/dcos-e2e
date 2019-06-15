# This works around https://github.com/coreos/bugs/issues/426
sudo mkdir -p /etc/systemd/system/sshd.service.d
sudo touch /etc/systemd/system/sshd.service.d/override.conf
sudo bash -c "echo '[Service]' >> /etc/systemd/system/sshd.service.d/override.conf"
sudo bash -c "echo 'Restart=always' >> /etc/systemd/system/sshd.service.d/override.conf"
# Without this we get:
# sshd.service: Start request repeated too quickly.
# Failed to start OpenSSH server daemon.
# sshd.service: Unit entered failed state.
# sshd.service: Failed with result 'start-limit-hit'.
sudo bash -c "echo 'RestartSec=3s' >> /etc/systemd/system/sshd.service.d/override.conf"
sudo systemctl restart sshd
sudo systemctl disable locksmithd
sudo systemctl stop locksmithd
sudo systemctl mask locksmithd
sudo systemctl disable update-engine # Disabling automatic updates.
sudo systemctl stop update-engine
sudo systemctl mask update-engine
sudo systemctl restart docker # Restarting docker to ensure its ready. Seems like its not during first usage
