# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.3] - 2023-04-20
### Changed
- Changed link hover color to dark cyan for readability and to match color
  scheme used in mermaid diagrams.

### Fixed
- Critical bug in root template that was preventing project names from
  appearing.

## [0.0.2] - 2023-04-19
### Changed
- Reworked `linear_api.PROJECTS_BY_TEAM_QUERY` to return up to 250 projects
  (previous limit was 50), filtering on only projects with "planned" or
  "started" state.
- New field `linear_api.Project.state` to store the project state.
- Projects are now color-coded by state in the project list.
- Reworked `linear_api.Team.projects` to be a dict (keys are project IDs)
  instead of a set of Projects.

## [0.0.1] - 2023-04-18
Initial release.

[0.0.3]: https://github.com/sclabs/lingraph/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/sclabs/lingraph/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/sclabs/lingraph/releases/tag/v0.0.1
