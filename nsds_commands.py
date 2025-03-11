from typing import Dict, List, Optional

class CommandStructure:
    def __init__(self):
        self.commands = {
            "auth": {
                "title": "Auth management for NFS/SMB services",
                "subcommands": {
                    "clean": "Remove the auth configuration",
                    "commit": "Commit the edited auth configuration",
                    "edit": "Edit the auth configuration",
                    "init": "Initialize the authentication configuration",
                    "show": "Display the current auth configuration"
                }
            },
            "cluster": {
                "title": "Cluster wide operations",
                "subcommands": {
                    "destroy": "Stop and remove nsds components from all the nodes in the cluster",
                    "init": "Create and initialize the NSDS cluster",
                    "rename": "Rename the cluster",
                    "restart": "Restart the NSDS services on all the nodes in the cluster",
                    "start": "Start the NSDS services on all the nodes in the cluster",
                    "status": "Display the cluster status",
                    "stop": "Stop the NSDS services on all the nodes in the cluster"
                }
            },
            "config": {
                "title": "Configuration management",
                "subcommands": {
                    "cluster": {
                        "title": "Cluster config operations",
                        "subcommands": {
                            "backup": "Backup the configurations of nsds components",
                            "list": "Display the current cluster configurations"
                        }
                    },
                    "docker": {
                        "title": "Control NSDS docker (container) parameters",
                        "subcommands": {
                            "list": "List docker runtime options",
                            "update": "Update docker runtime options"
                        }
                    },
                    "file": {
                        "title": "List/Edit various config files",
                        "subcommands": {
                            "list": "List the config files",
                            "update": "Update NSDS config file"
                        }
                    }
                }
            },
            "diag": {
                "title": "Diagnostics and debugging",
                "subcommands": {
                    "collect": "Collect the support bundle for nsds nodes",
                    "lustre": {
                        "title": "Manage Lustre client diagnostics and debug",
                        "subcommands": {
                            "debug": "Enable/disable debug for lustre client"
                        }
                    },
                    "nfs": {
                        "title": "Manage NFS service diagnostics and debug",
                        "subcommands": {
                            "debug": "Enable/disable debug for NFS service"
                        }
                    },
                    "smb": {
                        "title": "Manage SMB service diagnostics and debug",
                        "subcommands": {
                            "debug": "Enable/disable debug for SMB service"
                        }
                    }
                }
            },
            "export": {
                "title": "Export management",
                "subcommands": {
                    "nfs": {
                        "title": "NFS Export management",
                        "subcommands": {
                            "add": "Add a new export",
                            "list": "List exports",
                            "load": "Load exports from conf",
                            "remove": "Remove exports",
                            "show": "Show export(s)",
                            "update": "Update an existing export"
                        }
                    },
                    "smb": {
                        "title": "SMB Export management",
                        "subcommands": {
                            "add": "Add a new export",
                            "list": "List exports",
                            "load": "Load exports from conf",
                            "remove": "Remove exports",
                            "show": "Show export(s)",
                            "update": "Update an existing export"
                        }
                    }
                }
            },
            "filesystem": {
                "title": "File system (export root) management",
                "subcommands": {
                    "add": "Add a new file system",
                    "list": "List file system(s)",
                    "remove": "Remove a file system"
                }
            }
        }

    def get_main_categories(self) -> List[str]:
        """Get list of main command categories"""
        return list(self.commands.keys())

    def get_category_title(self, category: str) -> str:
        """Get the title for a category"""
        return self.commands.get(category, {}).get("title", "")

    def get_subcommands(self, category: str, subcategory: Optional[str] = None) -> Dict[str, str]:
        """Get subcommands for a category/subcategory"""
        if subcategory:
            return self.commands.get(category, {}).get("subcommands", {}).get(subcategory, {}).get("subcommands", {})
        return self.commands.get(category, {}).get("subcommands", {})

    def get_command_description(self, category: str, command: str) -> str:
        """Get description for a command"""
        subcommands = self.get_subcommands(category)
        return subcommands.get(command, "")
