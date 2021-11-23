import subprocess


def apply_camera_settings(camera: str) -> None:
    """Applies the specified settings to the camera.

    Args:
        camera (str): [description]
    """
    camera_settings = {}

    with open(f"cameras/{camera.split('/')[-1]}.txt", "r") as f:
        for line in f:
            camera_settings[line.lstrip().split(" ")[0]] = int(line.lstrip().split("value=")[-1].split(" ")[0])

    for key in camera_settings:
        subprocess.call(
            [f"v4l2-ctl -d {camera} --set-ctrl {key}={camera_settings[key]}"],
            shell=True,
        )
