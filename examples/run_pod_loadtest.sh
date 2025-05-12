#!/bin/bash

VM_IP="34.64.193.91"                              # ← 여기에 VM의 공인 IP 입력
USERNAME="goni"                                   # ← 사용자 이름
SSH_KEY_PATH="$HOME/.ssh/google_compute_engine"   # ← SSH private key 경로
COUNT=100                                         # 병렬 세션 수
NAMESPACE="test"                                  # ← 네임스페이스 이름

# SSH key 파일 존재 확인
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "Error: SSH key file not found at $SSH_KEY_PATH"
    exit 1
fi

# Namespace 생성
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no $USERNAME@$VM_IP "
  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
  kubectl create namespace $NAMESPACE
"

# 병렬 실행
seq 1 $COUNT | xargs -P $COUNT -I{} \
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no $USERNAME@$VM_IP "
  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
  kubectl apply -f - --namespace=$NAMESPACE <<EOF &
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod-{}
  labels:
    app: nginx-{}
spec:
  containers:
  - name: nginx
    image: nginx
    imagePullPolicy: IfNotPresent
EOF
"

# 완료 메시지 출력
echo "모든 pod 생성 요청이 비동기적으로 실행되었습니다."
echo "Pod 번호 범위: 1 ~ $COUNT"
