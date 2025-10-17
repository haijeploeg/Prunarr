{{/*
Expand the name of the chart.
*/}}
{{- define "prunarr.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "prunarr.fullname" -}}
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

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "prunarr.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "prunarr.labels" -}}
helm.sh/chart: {{ include "prunarr.chart" . }}
{{ include "prunarr.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "prunarr.selectorLabels" -}}
app.kubernetes.io/name: {{ include "prunarr.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "prunarr.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "prunarr.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the image name
*/}}
{{- define "prunarr.image" -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion }}
{{- printf "%s:%s" .Values.image.repository $tag }}
{{- end }}

{{/*
Create the name of the secret
*/}}
{{- define "prunarr.secretName" -}}
{{- if .Values.externalSecrets.enabled }}
{{- .Values.externalSecrets.secretName }}
{{- else }}
{{- include "prunarr.fullname" . }}-secret
{{- end }}
{{- end }}

{{/*
Create the name of the configmap
*/}}
{{- define "prunarr.configMapName" -}}
{{- include "prunarr.fullname" . }}-config
{{- end }}

{{/*
Create the name of the PVC
*/}}
{{- define "prunarr.pvcName" -}}
{{- if .Values.persistence.existingClaim }}
{{- .Values.persistence.existingClaim }}
{{- else }}
{{- include "prunarr.fullname" . }}-cache
{{- end }}
{{- end }}
