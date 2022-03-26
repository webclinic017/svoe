# TODO dummy placeholder pod for spot buffer
{{- define "data-feed.data-feed-service" }}
apiVersion: v1
kind: Service
metadata:
  labels:
    monitored-by: data-feed-servicemonitor
    name: {{ .name }}-svc
  name: {{ .name }}-svc
spec:
  clusterIP: None
  ports:
    - name: redis
      port: {{ .redis.port }}
      protocol: TCP
      targetPort: {{ .redis.port }}
    - name: redis-metrics
      port: 9121
      protocol: TCP
      targetPort: 9121
    - name: df-metrics
      port: {{ .dataFeed.prometheusMetricsPort }}
      protocol: TCP
      targetPort: {{ .dataFeed.prometheusMetricsPort }}
  selector:
    name: {{ .name }}-ss
{{- end }}
{{- define "data-feed.data-feed-stateful-set" }}
# TODO startup probe and port
apiVersion: apps/v1
kind: StatefulSet
metadata:
  labels:
    name: {{ .name }}-ss
  name: {{ .name }}-ss
spec:
  replicas: 1
  selector:
    matchLabels:
      name: {{ .name }}-ss
  serviceName: {{ .name }}-svc
  template:
    metadata:
      labels:
        name: {{ .name }}-ss
        {{- range $k, $v := .labels }}
        {{ $k }}: {{ $v | quote }}
        {{- end }}
    spec:
      # TODO set resources for redis/redis-exporter sidecars
      # TODO sync termination order (redis after data-feed)
      containers:
        - image: redis:alpine
          name: redis
          ports:
            - containerPort: {{ .redis.port }}
        - image: oliver006/redis_exporter:latest
          name: redis-exporter
          ports:
            - containerPort: 9121
              name: redis-metrics
        - image: {{ .dataFeed.image }}
          imagePullPolicy: IfNotPresent
          name: data-feed-container
          ports:
            - containerPort: {{ .dataFeed.prometheusMetricsPort }}
              name: df-metrics
            - containerPort: {{ .dataFeed.healthPort }}
              name: df-health
          volumeMounts:
            - mountPath: {{ .dataFeed.configVolumeMountPath }}
              name: {{ .name }}-conf-vol
          envFrom:
            - secretRef:
                name: data-feed-common-secret
          # TODO startup probe on the same /health endpoint
          livenessProbe:
            httpGet:
              path: {{ .dataFeed.healthPath }}
              port: df-health
            initialDelaySeconds: 50 # TODO figure out timeout (sometimes takes up to 2 minutes to start)
            periodSeconds: 5
          resources:
            requests:
              memory: {{ .dataFeed.resources.requests.memory }}
              cpu: {{ .dataFeed.resources.requests.cpu }}
            limits:
              memory: {{ .dataFeed.resources.limits.memory }}
              cpu: {{ .dataFeed.resources.limits.cpu }}
      terminationGracePeriodSeconds: 30
      volumes:
        - configMap:
            defaultMode: 365
            name: {{ .name }}-cm
          name: {{ .name }}-conf-vol
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: workload-type
                    operator: In
                    values:
                      - data-feed
                  - key: node-type
                    operator: In
                    values:
                      - spot
      tolerations:
        - key: node-type
          operator: Equal
          value: spot
          effect: NoSchedule
        - key: workload-type
          operator: Equal
          value: data-feed
          effect: NoSchedule
{{- end }}
{{- define "data-feed.data-feed-config-map" }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .name }}-cm
data:
  data-feed-config.yaml: |
  {{- .dataFeed.config | nindent 4 }}
{{- end }}