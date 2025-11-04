# 🚀 Guía de Despliegue en AWS EKS

## Requisitos Previos

- AWS CLI instalado y configurado
- kubectl instalado
- eksctl instalado (opcional pero recomendado)
- Docker instalado
- Acceso a AWS con permisos para EKS, ECR, Secrets Manager

---

## Paso 1: Crear Repositorios en ECR

```bash
# Crear repositorio para MCP Toolbox
aws ecr create-repository --repository-name mcp-toolbox --region us-east-1

# Crear repositorio para Agent
aws ecr create-repository --repository-name mcp-agent --region us-east-1
```

Guarda las URIs que te devuelve (ejemplo: `123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-toolbox`)

---

## Paso 2: Construir y Subir Imágenes Docker a ECR

```bash
# Login en ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build y push MCP Toolbox
cd mcp-server
docker build -t mcp-toolbox:latest .
docker tag mcp-toolbox:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-toolbox:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-toolbox:latest

# Build y push Agent
cd ../agent
docker build -t mcp-agent:latest .
docker tag mcp-agent:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-agent:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-agent:latest
```

---

## Paso 3: Crear Cluster EKS (si no existe)

### Opción A: Con eksctl (recomendado)

```bash
eksctl create cluster \
  --name mcp-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 3 \
  --managed
```

### Opción B: Usar cluster existente

```bash
# Configurar kubectl para tu cluster
aws eks update-kubeconfig --region us-east-1 --name tu-cluster-existente
```

---

## Paso 4: Configurar Secrets Manager

```bash
# Crear secret con credenciales AWS para Bedrock
aws secretsmanager create-secret \
  --name mcp-agent-credentials \
  --description "AWS credentials for MCP Agent Bedrock access" \
  --secret-string '{
    "AWS_REGION":"us-east-1",
    "AWS_ACCESS_KEY_ID":"",
    "AWS_SECRET_ACCESS_KEY":"",
    "BEDROCK_MODEL_ID":"us.amazon.nova-pro-v1:0"
  }' \
  --region us-east-1
```

---

## Paso 5: Configurar IAM Role para ServiceAccount

```bash
# Crear IAM OIDC provider para el cluster
eksctl utils associate-iam-oidc-provider \
  --cluster mcp-cluster \
  --region us-east-1 \
  --approve

# Crear IAM Policy para Secrets Manager y Bedrock
cat > mcp-agent-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:mcp-agent-credentials-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name MCPAgentPolicy \
  --policy-document file://mcp-agent-policy.json

# Crear ServiceAccount con IAM Role
eksctl create iamserviceaccount \
  --name mcp-agent-sa \
  --namespace default \
  --cluster mcp-cluster \
  --region us-east-1 \
  --attach-policy-arn arn:aws:iam::123456789012:policy/MCPAgentPolicy \
  --approve
```

---

## Paso 6: Crear Manifiestos de Kubernetes

Ya están creados en la carpeta `k8s/`. Actualiza las URIs de las imágenes:

```bash
# En k8s/mcp-toolbox-deployment.yaml
# Reemplaza: 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-toolbox:latest

# En k8s/agent-deployment.yaml
# Reemplaza: 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-agent:latest
```

---

## Paso 7: Desplegar en EKS

```bash
# Aplicar todos los manifiestos
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/mcp-toolbox-deployment.yaml
kubectl apply -f k8s/mcp-toolbox-service.yaml
kubectl apply -f k8s/agent-deployment.yaml
kubectl apply -f k8s/agent-service.yaml

# Verificar que los pods estén corriendo
kubectl get pods -n mcp-system

# Ver los servicios
kubectl get svc -n mcp-system
```

---

## Paso 8: Exponer el Agent (Opcional)

### Opción A: LoadBalancer (público)

```bash
kubectl expose deployment agent \
  --type=LoadBalancer \
  --name=agent-lb \
  --port=80 \
  --target-port=8000 \
  -n mcp-system

# Obtener la URL pública
kubectl get svc agent-lb -n mcp-system
```

### Opción B: Ingress (recomendado para producción)

```bash
# Instalar AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=mcp-cluster

# Aplicar Ingress
kubectl apply -f k8s/ingress.yaml

# Obtener la URL
kubectl get ingress -n mcp-system
```

---

## Paso 9: Verificar el Despliegue

```bash
# Ver logs del toolbox
kubectl logs -f deployment/mcp-toolbox -n mcp-system

# Ver logs del agent
kubectl logs -f deployment/agent -n mcp-system

# Hacer port-forward para testing
kubectl port-forward svc/agent 8001:8000 -n mcp-system

# Probar desde tu máquina local
curl http://localhost:8001/health
```

---

## Paso 10: Probar el Sistema

```powershell
# Si usaste LoadBalancer, usa la URL externa
$LB_URL = kubectl get svc agent-lb -n mcp-system -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Probar health check
Invoke-WebRequest -Uri "http://${LB_URL}/health"

# Probar suma
$body = '{"input":"Suma 100 y 50"}'
Invoke-WebRequest -Uri "http://${LB_URL}/process" -Method POST -Body $body -ContentType "application/json"
```

---

## 🔄 Actualizar la Aplicación

```bash
# 1. Build nueva imagen
docker build -t mcp-agent:v2 ./agent

# 2. Tag y push
docker tag mcp-agent:v2 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-agent:v2
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-agent:v2

# 3. Actualizar deployment
kubectl set image deployment/agent agent=123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-agent:v2 -n mcp-system

# 4. Verificar rollout
kubectl rollout status deployment/agent -n mcp-system
```

---

## 📊 Monitoreo y Logs

```bash
# Ver métricas de pods
kubectl top pods -n mcp-system

# Ver eventos
kubectl get events -n mcp-system --sort-by='.lastTimestamp'

# Streaming logs
kubectl logs -f deployment/agent -n mcp-system --tail=100

# Logs de múltiples pods
kubectl logs -l app=agent -n mcp-system --tail=50
```

---

## 🔒 Seguridad (Recomendaciones)

1. **Network Policies**: Limitar comunicación entre pods
```bash
kubectl apply -f k8s/network-policy.yaml
```

2. **Pod Security Standards**: Aplicar políticas restrictivas
```bash
kubectl label namespace mcp-system pod-security.kubernetes.io/enforce=restricted
```

3. **Secrets**: Nunca commitear credenciales, usar Secrets Manager

4. **RBAC**: Crear roles específicos para cada servicio

5. **TLS**: Usar certificados para comunicación interna

---

## 🐛 Troubleshooting

### Pods no inician
```bash
kubectl describe pod <pod-name> -n mcp-system
kubectl logs <pod-name> -n mcp-system --previous
```

### Problemas de red
```bash
# Verificar DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup mcp-toolbox.mcp-system.svc.cluster.local

# Verificar conectividad
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl http://mcp-toolbox:8000/health
```

### Error de credenciales
```bash
# Verificar ServiceAccount
kubectl describe sa mcp-agent-sa -n mcp-system

# Verificar secrets
kubectl get secrets -n mcp-system
```

---

## 💰 Costos Estimados (us-east-1)

- **EKS Cluster**: ~$73/mes (control plane)
- **EC2 t3.medium x2**: ~$60/mes
- **ECR Storage**: ~$1/mes (< 10GB)
- **Data Transfer**: Variable
- **Bedrock Nova Pro**: Pay per request

**Total estimado**: ~$150-200/mes

---

## 📚 Recursos Adicionales

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
