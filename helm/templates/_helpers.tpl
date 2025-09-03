{{/*
Sanitize name for environment variable usage
*/}}
{{- define "rag-lsd.envVarName" -}}
{{- . | replace " " "_" | replace "-" "_" | replace "." "_" | replace "/" "_" | replace ":" "_" | upper -}}
{{- end -}}

{{/*
Expand the name of the chart.
*/}}
{{- define "rag-lsd.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "rag-lsd.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}