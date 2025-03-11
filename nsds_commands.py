from typing import Dict, List, Optional, Tuple

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

    def search_commands(self, query: str) -> List[Tuple[str, str, str]]:
        """
        Search through all commands and subcommands
        Returns: List of tuples (full_path, command_type, description)
        """
        results = []
        query = query.lower()

        def search_nested(category: str, data: dict, current_path: List[str]):
            if "title" in data:
                title = data["title"].lower()
                if query in title:
                    results.append((" ".join(current_path), "category", data["title"]))

            if "subcommands" in data:
                subcommands = data["subcommands"]
                for cmd, value in subcommands.items():
                    cmd_path = current_path + [cmd]
                    if isinstance(value, dict):
                        search_nested(category, value, cmd_path)
                    else:
                        if query in cmd.lower() or query in value.lower():
                            results.append((" ".join(cmd_path), "command", value))

        # Search through all categories
        for category, data in self.commands.items():
            if query in category.lower():
                results.append((category, "category", data.get("title", "")))
            search_nested(category, data, [category])

        return results

    def get_command_description(self, category: str, command: str) -> str:
        """Get description for a command"""
        subcommands = self.get_subcommands(category)
        return subcommands.get(command, "")