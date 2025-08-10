<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brave_dark.png">
    <source media="(prefers-color-scheme: light)" srcset="brave_light.png">
    <img alt="Brave Logo" src="brave_light.png">
  </picture>
</p>

another-brave-overlay
=====================

![⚙️ Update ebuilds](https://img.shields.io/github/actions/workflow/status/falbrechtskirchinger/another-brave-overlay/update-ebuilds.yml?style=flat-square&logo=github&label=%E2%9A%99%EF%B8%8F%20Update%20ebuilds)
![🧪 Merge ebuild (stable)](https://img.shields.io/github/actions/workflow/status/falbrechtskirchinger/another-brave-overlay/test-stable.yml?style=flat-square&logo=github&label=%F0%9F%A7%AA%20Merge%20ebuild%20(stable))
![🧪 Merge ebuild (beta)](https://img.shields.io/github/actions/workflow/status/falbrechtskirchinger/another-brave-overlay/test-beta.yml?style=flat-square&logo=github&label=%F0%9F%A7%AA%20Merge%20ebuild%20(beta))
![🧪 Merge ebuild (nightly)](https://img.shields.io/github/actions/workflow/status/falbrechtskirchinger/another-brave-overlay/test-nightly.yml?style=flat-square&logo=github&label=%F0%9F%A7%AA%20Merge%20ebuild%20(nightly))

This Gentoo overlay provides automatically generated ebuilds for the [Brave browser](https://brave.com/), a privacy-focused, open-source web browser based on Chromium. The ebuilds are based on the official Gentoo Google Chrome ebuilds, adapted to deliver the stable, beta, and nightly versions of Brave via the following ebuilds:

- `www-client/brave-browser` (stable)
- `www-client/brave-browser-beta` (beta)
- `www-client/brave-browser-nightly` (nightly)

These ebuilds install pre-built binary versions of Brave, similar to the Google Chrome ebuilds in the main Gentoo repository.

Installation
------------

To install Brave from this overlay, follow these steps:

1. Add the overlay:

    ```sh
    eselect repository add another-brave-overlay git https://github.com/falbrechtskirchinger/another-brave-overlay.git
    ```

2. Sync the overlay to download the ebuilds:

    ```sh
    emaint sync -r another-brave-overlay
    ```

3. Install Brave from the desired release channel using `emerge`. Available packages are:

    - `www-client/brave-browser` (stable)
    - `www-client/brave-browser-beta` (beta)
    - `www-client/brave-browser-nightly` (nightly)

    For example, to install the stable version:

    ```sh
    emerge -av www-client/brave-browser
    ```

Issues and Contributions
------------------------

If you encounter any problems or have suggestions for improvement, please open an issue on the GitHub repository: https://github.com/falbrechtskirchinger/another-brave-overlay.

Contributions are welcome! You can contribute by:

- Forking the repository on GitHub.
- Making your changes or enhancements.
- Submitting a pull request.

License
-------

Ebuilds in this overlay are licensed under the GNU General Public License v2.0 (GPL-2). Scripts and other files are licensed under the MIT License (MIT).

See the `LICENSE.GPL-2` and `LICENSE.MIT` files in the repository for full details.

**Trademark Notice**: All Brave logos, marks, and designations are trademarks or registered trademarks of Brave Software, Inc.
