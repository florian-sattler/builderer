# arguments in parameters and cli
arg_registry_title = "Registry URL"
arg_registry_desc = "Set the registry url. You may include a port using the colon notation (example.com:3000/). This is needed when using a non standard port. Unset by default."
arg_prefix_title = "Registry directory"
arg_prefix_desc = "Set the directory for all images. This is the image component between registry url and image name. For example on docker hub this is used for the username. Unset by default."
arg_push_title = "Allow pushing images"
arg_push_desc = "Whether to allow pushing images."
arg_cache_title = "Allow caching images"
arg_cache_desc = "Whether to allow using cached images. This is especially usefull for local builds."
arg_verbose_title = "Verbose output"
arg_verbose_desc = "Show issued commands and their live output."
arg_tags_title = "Tags to use"
arg_tags_desc = "One or multiple tags to use for each image. Default to ['latest']"
arg_simulate_title = "Simulate execution"
arg_simulate_desc = "Prevent issuing any commands just do the printing."
arg_backend_title = "Build Backend"
arg_backend_desc = "Overwrite the backend used to build, tag and pull images. Defaults to 'docker'"

# just cli
arg_cli_config = "Path to %(prog)s yaml configuration file. Defaults to '.builderer.yml'"
arg_cli_no_push = "Prevent pushing images in all steps."

# just parameters
conf_parameters = "Overwrite default parameters. Values set here will be overwritten by command line arguments."
conf_steps = "List of steps to execute."

# steps
step_type = "Type of the step"

step_action_name = "Name printed before running the action"
step_action_commands = "List of commands. Each command is a list of strings: the executable followed by arguments."
step_action_post = "Whether to add the action to the post queue"

step_build_directory = "Directory containing the Dockerfile. This is also used as the build context."
step_build_directories = "Directories containing each containing Dockerfile."
step_build_dockerfile = "Path to Dockerfile. Name of the resulting image. Defaults to <directory>/Dockerfile."
step_build_name = "Name of the resulting image. Defaults to the name of the Dockerfiles parent directory."
step_build_push = "Whether to push the image. Defaults to True."
step_build_qualified = "Whether to add the registry path and prefix to the image name. Defaults to True."

step_extract_image = "Name of the image to copy from."
step_extract_path = "Source path inside the image."
step_extract_dest = "Destination paths. The file will be copied to all destinations individually."

step_forward_name = "Image name to forward."
step_forward_new_name = (
    "Set a new name for the image. By default the basename of the pulled image without the tag is used."
)

step_pull_name = "Image name to pull."
step_pull_names = "Image names to pull."
