local ext = get_current_extension_info()

project_ext (ext)

repo_build.prebuild_link {
    { "lightspeed", ext.target_dir.."/lightspeed" },
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
    { "icons", ext.target_dir.."/icons" }
}
