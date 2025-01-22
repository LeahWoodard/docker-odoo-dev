### Project Template README: Debug Odoo with Docker in VSCode

#### Overview
This project template facilitates Odoo development using Docker, specifically configured for VSCode IDE. It includes setup instructions and tips for effective debugging using the Odoo IDE extension.

#### Prerequisites
Before proceeding, ensure you have the following installed:
1. Docker
2. Git
3. VSCode with the following extensions:
   - Docker
   - Odoo IDE
   - Python Debugger

#### Setup Steps

1. **Clone the Project**
   ```bash
   git clone https://github.com/teguhteja/docker-odoo-dev.git -b 17
   ```

2. **Get Odoo Stubs**
   Run the script to fetch the `odoo-stub` folder:
   ```bash
   ./git-clone-odoo-stubs.sh
   ```

3. **Build Docker Image**
   Build the Odoo development image:
   ```bash
   docker build -t odoodev:17 .
   ```

4. **Start Docker Compose**
   Launch Odoo 17 and PostgreSQL 16 containers:
   ```bash
   docker compose up -d
   ```

5. **Add Your Addons**
   Place your addons in the `custom_addons` folder and restart the Docker stack (`docker compose restart odoo-dev`) using docker extension vscode.

6. **Debugging**
   - Set breakpoints in your source code within VSCode.
   - Ensure the debugger is configured to debug external code (`"justMyCode": false` in launch.json).
   - Access the Odoo source code from the container:
     ```bash
     ./docker-cp-odoo.sh
     ```
   - Add breakpoints in the Odoo source code.
   - Run the debugger process to start debugging.

#### Troubleshooting Tips

1. **Copying misc.py in odoodev**
   If backup failures occur with Docker images, modify `misc.py` to resolve issues.

2. **Debugging Odoo Source Code**
   Modify `"justMyCode": false` in `launch.json`, 
   download the Odoo folder from the container using `docker-cp-odoo.sh`,
   uncomment this line in docker-compose.yml
   `- ./odoo:/usr/lib/python3/dist-packages/odoo` 
   restart stack or docker compose
   add breakpoints, and start the debugger process .

#### Conclusion
This README provides detailed steps to set up an Odoo development environment using Docker and VSCode, enabling efficient debugging of Odoo applications. For further details, refer to the full documentation and scripts available in the project repository.

---

For detailed scripts and further instructions, visit [docker-odoo-dev](https://github.com/teguhteja/docker-odoo-dev.git).