import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Title, Text, Loader, Center, Container, Paper, Stack, 
  Button, Group, Divider, Badge, Breadcrumbs, Anchor, Alert
} from '@mantine/core';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, Info, Clock } from 'lucide-react';
import apiClient from '../../api/client';

interface SOPDetail {
  id: number;
  title: string;
  category: string;
  content: string;
  status: string;
  current_version_number: number;
  updated_at: string;
}

export const SOPDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: sop, isLoading, error } = useQuery<SOPDetail>({
    queryKey: ['sop', id],
    queryFn: async () => {
      const response = await apiClient.get(`/sops/${id}`);
      return response.data;
    },
  });

  const acknowledgeMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post(`/sops/${id}/acknowledge`);
    },
    onSuccess: () => {
      // Re-fetch to update status or just show success
      queryClient.invalidateQueries({ queryKey: ['sop', id] });
    },
  });

  if (isLoading) return <Center h="100vh"><Loader /></Center>;
  
  if (error || !sop) {
    return (
      <Container size="md" py="xl">
        <Alert icon={<Info size={16} />} title="Erro" color="red">
          Não foi possível carregar o procedimento. Ele pode ter sido removido ou você não tem permissão.
        </Alert>
        <Button leftSection={<ArrowLeft size={16} />} variant="subtle" mt="md" onClick={() => navigate(-1)}>
          Voltar
        </Button>
      </Container>
    );
  }

  const items = [
    { title: 'Dashboard', href: '/' },
    { title: 'Planos de Saúde', href: '/health-plans' },
    { title: 'Procedimentos', href: '#' },
  ].map((item, index) => (
    <Anchor href={item.href} key={index} onClick={(e) => {
      if (item.href !== '#') {
        e.preventDefault();
        navigate(item.href);
      }
    }}>
      {item.title}
    </Anchor>
  ));

  return (
    <Container size="md" py="xl">
      <Stack gap="lg">
        <Breadcrumbs>{items}</Breadcrumbs>

        <Group justify="space-between" align="flex-start">
          <Stack gap={4}>
            <Title order={1}>{sop.title}</Title>
            <Group gap="xs">
              <Badge color="blue" variant="light">{sop.category}</Badge>
              <Badge color="gray" variant="outline">Versão {sop.current_version_number}</Badge>
              <Group gap={4} ml="xs">
                <Clock size={14} color="gray" />
                <Text size="xs" c="dimmed">
                  Atualizado em: {new Date(sop.updated_at).toLocaleDateString('pt-BR')}
                </Text>
              </Group>
            </Group>
          </Stack>
          
          <Button 
            leftSection={<ArrowLeft size={16} />} 
            variant="default" 
            onClick={() => navigate(-1)}
          >
            Voltar
          </Button>
        </Group>

        <Paper withBorder p="xl" radius="md" shadow="sm">
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: sop.content }} 
          />
        </Paper>

        <Divider />

        <Paper p="md" radius="md" withBorder bg="var(--mantine-color-blue-light)">
          <Group justify="space-between">
            <Stack gap={4}>
              <Text fw={600}>Confirmação de Leitura</Text>
              <Text size="sm" c="dimmed">
                Ao clicar no botão ao lado, você confirma que leu e compreendeu este procedimento operacional.
              </Text>
            </Stack>
            <Button 
              color="blue" 
              leftSection={<CheckCircle size={18} />}
              onClick={() => acknowledgeMutation.mutate()}
              loading={acknowledgeMutation.isPending}
            >
              Li e Estou Ciente
            </Button>
          </Group>
        </Paper>
      </Stack>
    </Container>
  );
};
