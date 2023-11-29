import argparse
import logging
import platform
from config_module.config_io import (
    load_configuration
)
from service_module.service_management import (
    install_service,
    uninstall_service,
    start_service,
    stop_service,
    restart_service,
    check_service_status,
    is_service_installed

)

os_type = platform.system().lower()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

if os_type == "windows":
    from service_module.windows_service import RewstWindowsService


def main():
    parser = argparse.ArgumentParser(description='Rewst Service Manager.')
    parser.add_argument('--org-id', required=True, help='Organization ID')
    parser.add_argument('--config-file', help='Path to the configuration file')
    parser.add_argument('--install', action='store_true', help='Install the service')
    parser.add_argument('--uninstall', action='store_true', help='Uninstall the service')
    parser.add_argument('--status', action='store_true', help='Check the service status')
    parser.add_argument('--start', '-s', action='store_const', const=True, default=False, help='Start the service')
    parser.add_argument('--stop', action='store_true', help='Stop the service')
    parser.add_argument('--restart', action='store_true', help='Restart the service')

    args = parser.parse_args()

    # Load configuration if config file path is provided
    if args.config_file:
        load_configuration(None,args.config_file)

    # Set the service name based on the organization ID
    if os_type == "windows":
        RewstWindowsService.set_service_name(args.org_id)

    # Perform the requested service action
    if args.install:
        install_service(args.org_id)
        start_service(args.org_id)
    elif args.uninstall:
        uninstall_service(args.org_id)
    elif args.start:
        start_service(args.org_id)
    elif args.stop:
        stop_service(args.org_id)
    elif args.restart:
        restart_service(args.org_id)
    elif args.status:
        is_service_installed(args.org_id)
        check_service_status(args.org_id)
    else:
        print("No action specified. Use --install, --uninstall, --start, --stop, --status, or --restart.")


if __name__ == "__main__":
    main()
