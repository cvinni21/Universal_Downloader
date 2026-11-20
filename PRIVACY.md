# Privacy Policy — Universal Downloader Bridge

Last updated: 20 November 2026

Universal Downloader Bridge is a browser extension that sends a link chosen by the user to the Universal Downloader desktop application installed on the same computer.

## Information handled

- When the user chooses a context-menu command, the extension reads the selected page URL, link URL, or selected text that looks like a web address.
- If the user turns on **Interceptar downloads**, the extension reads the URL of a browser download and forwards it to the local desktop application. This setting is off by default.
- The extension stores the interception preference and a short status message in the browser's local extension storage.

## Where information goes

URLs are sent only to the locally installed Universal Downloader native-messaging helper so the desktop application can start the requested download. The extension does not send browsing URLs, download history, or other personal data to Universal Downloader servers, analytics services, or advertising networks. The extension does not sell or share this information with third parties.

The Universal Downloader desktop application makes its own HTTPS request to the public GitHub Releases API when it checks for updates. That update check is separate from the extension and is described in the project README.

## User control and retention

Automatic interception is disabled until the user enables it in the extension popup. The user can disable it at any time. The extension keeps the preference and status locally in the browser. The local helper places received links in a temporary inbox under the current Windows user's application-data folder; the desktop app removes each inbox item after reading it. Downloaded media is saved to the destination selected in the desktop app.

## Permissions

- **Context menus:** add commands to send the current page, a link, or a selected URL.
- **Downloads:** read a download URL only for the optional interception feature; when enabled, the matching browser download is cancelled after the local app accepts it.
- **Native messaging:** pass the user's selected URL to the locally installed desktop helper.
- **Storage:** remember the interception toggle and show the last operation's status.

## Contact

For questions or privacy requests, open an issue in the [Universal Downloader repository](https://github.com/cvinni21/Universal_Downloader/issues).
