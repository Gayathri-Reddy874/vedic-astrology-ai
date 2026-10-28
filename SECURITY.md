# Security

Please report vulnerabilities privately through GitHub's "Report a vulnerability" button on the Security tab rather than a public issue.

Operational notes: set a strong `SECRET_KEY`, keep `OPENAI_API_KEY` in the environment (never in git), and run behind HTTPS. Set `TRUST_PROXY=1` only behind a proxy you control.

